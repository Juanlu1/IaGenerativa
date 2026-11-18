"""Casos con respuesta para optimizar el prompt (Parte 3) sin usar los 50 casos de práctica.

Arma un caso del kit (`admision.casos.Caso`) por cada fila `correcta` del historial (historial_clasificado.csv +
historial/historial.csv + historial/trazas.jsonl) y le calcula la ficha esperada con las normas original, b y c.

- **Reconstrucción.** Los datos del triage salen de la fila; el nombre, el paciente y el motivo por el que no puede
  responder salen de la nota de triage de la traza. Lo que contestan el paciente o la entidad sale de lo que el
  operador preguntó y verificó en la traza. Se descarta la fila si la nota de triage que arma el entorno del kit con
  el caso reconstruido no es idéntica, carácter por carácter, a la que vio el operador.
- **Ficha esperada.** `etiquetar` aplica las secciones que deciden la ficha (NOR-ADM-01 a 03, NOR-COB-01 a 04,
  NOR-TDE-01 a 04) con los parámetros de cada versión, más las dos costumbres de costumbres.md (preferir la prepaga
  con dos credenciales y el aviso al voluntariado desde los 75 años sin acompañante).
- **Controles.** `etiquetar` se valida contra las 150 fichas esperadas de la práctica (50 casos x 3 versiones): ahí
  la práctica solo sirve para comprobar el etiquetador, no para optimizar. Además, en cada fila del historial la ficha
  calculada con las normas original tiene que coincidir con la que registró el operador, y la entidad a verificar con
  la que verificó; si no, la fila se descarta.

    uv run python casos_optimizacion.py     # valida y muestra cuántos casos quedan
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

import yaml

from admision.casos import Caso, cargar_casos, cargar_esperadas
from admision.comparar import comparar
from admision.entorno import CAMPOS, nota_de_triage

RAIZ = Path(__file__).resolve().parent
VERSIONES = ("original", "b", "c")
EDAD_VOLUNTARIADO = 75  # costumbre del historial (costumbres.md), no está en las normas

MOTIVO_ECG = "dolor torácico"
MOTIVO_ACV = "signos neurológicos focales de inicio súbito"
SEPSIS_GRAVE = ("probable", "con signos de shock")


def parametros(version: str) -> dict[str, int]:
    datos = yaml.safe_load((RAIZ / "normas" / version / "parametros.yaml").read_text(encoding="utf-8"))
    return {p["codigo"]: int(p["valor"]) for p in datos["parametros"]}


def _digitos(texto: str) -> str:
    return "".join(ch for ch in str(texto) if ch.isdigit())


# --- ficha esperada ----------------------------------------------------------------------------------------------

def cobertura_elegida(c: Caso) -> tuple[str, str, str] | None:
    """La obra social o prepaga que cuenta: la credencial (la prepaga si hay dos) o, sin credencial, lo que declara
    el paciente o su acompañante. Sin nadie que pueda responder, ninguna (NOR-COB-01 §3)."""
    if c.credenciales:
        prepagas = [x for x in c.credenciales if x[0] == "prepaga"]
        return prepagas[0] if prepagas else c.credenciales[0]
    if c.puede_responder or c.acompanante:
        return c.declarada
    return None


def etiquetar(c: Caso, p: dict[str, int]) -> dict:
    """La ficha esperada y la verificación, con el formato de practica/esperadas-*.jsonl."""
    documento = bool(c.documento_numero)
    registro = "definitivo" if documento else "provisorio"
    if documento and c.documento_tipo in ("pasaporte", "cédula") and c.nivel <= p["P-ADM-3"]:
        registro = "provisorio"  # NOR-ADM-03

    if c.motivo == MOTIVO_ECG:
        circuito, plazo = "ecg", p["P-TDE-1"]
    elif c.motivo == MOTIVO_ACV:
        circuito, plazo = "codigo_acv", p["P-TDE-2"]
    elif c.sepsis != "no":
        circuito, plazo = "codigo_sepsis", p["P-TDE-3"] if c.sepsis in SEPSIS_GRAVE else p["P-TDE-4"]
    else:
        circuito, plazo = "ninguno", None
    if plazo is not None and c.llegada == "en ambulancia":
        plazo -= p["P-TDE-5"]  # NOR-TDE-04

    entidades_del_paciente = [x[1] for x in c.credenciales] + ([c.declarada[1]] if c.declarada else [])
    if c.trabajo:  # NOR-COB-02 §5: cubre la ART
        cobertura, entidad = "art", c.art[0]
        requerida = [c.art[0], c.art[1]]
    else:
        elegida = cobertura_elegida(c)
        if elegida is None:
            cobertura, entidad, requerida = "sin_cobertura", None, None
        else:
            tipo, entidad, numero = elegida
            requerida = [entidad, numero]
            if _digitos(numero).endswith(str(p["P-COB-2"])):
                cobertura = "sin_cobertura"  # NOR-COB-04: terminación reservada, se notifica igual
            elif c.afiliaciones.get(f"{entidad}|{numero}", False):
                cobertura = tipo
            else:
                cobertura, entidad = "sin_cobertura", None  # NOR-COB-03 §4
    prohibidas = list(dict.fromkeys(e for e in entidades_del_paciente if requerida is None or e != requerida[0]))
    return {
        "ficha": {
            "registro": registro,
            "numero_documento": c.documento_numero,
            "box_antes_del_registro": c.nivel <= p["P-ADM-1"] or c.edad >= p["P-ADM-2"],
            "circuito": circuito,
            "plazo_circuito_min": plazo,
            "cobertura": cobertura,
            "entidad_a_notificar": entidad,
            "aviso_al_voluntariado": c.edad >= EDAD_VOLUNTARIADO and not c.acompanante,
        },
        "verificacion": {"requerida": requerida, "prohibidas": prohibidas},
    }


def validar_contra_practica() -> dict[str, int]:
    """Cuántas de las 50 fichas esperadas de la práctica reproduce `etiquetar`, por versión (9 controles)."""
    casos = cargar_casos(RAIZ / "practica" / "casos.jsonl")
    resultado = {}
    for version in VERSIONES:
        esperadas = cargar_esperadas(RAIZ / "practica" / f"esperadas-{version}.jsonl")
        p = parametros(version)
        bien = 0
        for c in casos:
            calculada = etiquetar(c, p)
            bien += (calculada["ficha"] == esperadas[c.id]["ficha"]
                     and calculada["verificacion"]["requerida"] == esperadas[c.id]["verificacion"]["requerida"]
                     and sorted(calculada["verificacion"]["prohibidas"])
                     == sorted(esperadas[c.id]["verificacion"]["prohibidas"]))
        resultado[version] = bien
    return resultado


# --- casos desde el historial ------------------------------------------------------------------------------------

def _cobertura(texto: str) -> tuple[str, str, str] | None:
    """'Entidad (obra social) número' -> (tipo, entidad, número)."""
    m = re.match(r"\s*(.+?)\s+\((obra social|prepaga)\)\s+(.+?)\s*$", texto or "")
    if not m:
        return None
    return ("obra_social" if m.group(2) == "obra social" else "prepaga", m.group(1).strip(), m.group(3).strip())


def _art(texto: str) -> tuple[str, str] | None:
    m = re.match(r"\s*(.+?)\s+CUIL\s+(.+?)\s*$", texto or "")
    return (m.group(1).strip(), m.group(2).strip()) if m else None


_VERIFICACION = re.compile(r"^(.+?) informa que la afiliación (.+?) está (activa|inactiva)\.$")


def _ficha_de_fila(fila: dict) -> dict:
    plazo = fila["plazo_circuito_min"].strip()
    return {
        "registro": fila["registro"],
        "numero_documento": fila["numero_documento"] or None,
        "box_antes_del_registro": fila["box_antes_del_registro"] == "sí",
        "circuito": fila["circuito"],
        "plazo_circuito_min": int(plazo) if plazo else None,
        "cobertura": fila["cobertura"],
        "entidad_a_notificar": fila["entidad_a_notificar"] or None,
        "aviso_al_voluntariado": fila["aviso_al_voluntariado"] == "sí",
    }


def caso_de_fila(fila: dict, traza: dict) -> Caso | None:
    """El caso del kit que corresponde a una fila del historial, o None si no se puede reconstruir exacto."""
    pasos = traza["pasos"]
    triage = next((x["resultado"] for x in pasos if x["herramienta"] == "leer_triage"), None)
    if triage is None:
        return None
    nombre = re.search(r"^Paciente: (.+), \d+ años\.$", triage, re.MULTILINE)
    no_responde = re.search(r"^Puede responder preguntas: no \((.+)\)\.$", triage, re.MULTILINE)
    acompanante = re.search(r"^Acompañante: (.+)\.$", triage, re.MULTILINE)
    trabajo = fila["lesion_trabajo"] if fila["lesion_trabajo"] != "no" else None
    credenciales = tuple(x for parte in fila["credenciales"].split(";") if (x := _cobertura(parte)))

    afiliaciones: dict[str, bool] = {}
    for paso in pasos:
        if paso["herramienta"] == "verificar_afiliacion":
            m = _VERIFICACION.match(str(paso["resultado"]))
            if m:
                afiliaciones[f"{m.group(1)}|{paso['argumentos'].get('numero_afiliado', m.group(2))}"] = (
                    m.group(3) == "activa")

    declarada = _cobertura(fila["cobertura_declarada"])
    if declarada is None and credenciales:
        # El operador no preguntó porque había credencial; el paciente declararía la que cuenta.
        prepagas = [x for x in credenciales if x[0] == "prepaga"]
        declarada = prepagas[0] if prepagas else credenciales[0]
    art = _art(fila["art_declarada"]) if trabajo else None
    if trabajo and art is None:
        return None
    try:
        caso = Caso(
            id=f"hist-{fila['id']}", paciente_id=traza["paciente_id"], nombre=nombre.group(1) if nombre else "",
            edad=int(fila["edad"]), nivel=int(fila["nivel"]), motivo=fila["motivo"], nota=fila["nota_enfermeria"],
            sepsis=fila["sospecha_sepsis"], llegada=fila["llegada"],
            documento_tipo=fila["documento_tipo"] or None, documento_numero=fila["documento_numero"] or None,
            credenciales=credenciales, puede_responder=fila["puede_responder"] == "sí",
            no_responde_porque=no_responde.group(1) if no_responde else None,
            acompanante=acompanante.group(1) if acompanante and acompanante.group(1) != "ninguno" else None,
            trabajo=trabajo, declarada=declarada, art=art, afiliaciones=afiliaciones)
    except (TypeError, ValueError):
        return None
    return caso if nota_de_triage(caso) == triage else None


def casos_del_historial() -> tuple[list[tuple[Caso, dict[str, dict]]], Counter]:
    """[(caso, {version: esperada})] de las filas correctas que pasan los controles, y por qué se descartó el resto."""
    tipos = {f["id"]: f["tipo"] for f in csv.DictReader((RAIZ / "historial_clasificado.csv").open(encoding="utf-8"))}
    filas = list(csv.DictReader((RAIZ / "historial" / "historial.csv").open(encoding="utf-8")))
    trazas = [json.loads(x) for x in (RAIZ / "historial" / "trazas.jsonl").read_text(encoding="utf-8").splitlines()
              if x.strip()]
    params = {v: parametros(v) for v in VERSIONES}
    casos, descartes = [], Counter()
    for fila, traza in zip(filas, trazas, strict=True):
        if tipos.get(fila["id"]) != "correcta":
            continue
        caso = caso_de_fila(fila, traza)
        if caso is None:
            descartes["no se pudo reconstruir el caso"] += 1
            continue
        esperadas = {v: {"caso": caso.id, **etiquetar(caso, params[v])} for v in VERSIONES}
        if esperadas["original"]["ficha"] != _ficha_de_fila(fila):
            descartes["la ficha calculada no coincide con la del operador"] += 1
            continue
        # La verificación del operador (su log) tiene que aprobar el control de verificación calculado.
        log = [{"herramienta": x["herramienta"], "argumentos": x["argumentos"], "valida": True} for x in traza["pasos"]]
        if not comparar(esperadas["original"], _ficha_de_fila(fila), log)["controles"]["verificacion"]:
            descartes["la verificación calculada no coincide con la del operador"] += 1
            continue
        casos.append((caso, esperadas))
    return casos, descartes


def main() -> None:
    print("etiquetar vs. fichas esperadas de la práctica:",
          {v: f"{n}/50" for v, n in validar_contra_practica().items()})
    casos, descartes = casos_del_historial()
    print(f"casos del historial: {len(casos)} de {sum(descartes.values()) + len(casos)} filas correctas")
    for motivo, n in descartes.most_common():
        print(f"  descartadas: {n} ({motivo})")
    print("circuitos:", dict(Counter(e["original"]["ficha"]["circuito"] for _, e in casos)))
    print("coberturas:", dict(Counter(e["original"]["ficha"]["cobertura"] for _, e in casos)))
    assert set(CAMPOS) == set(casos[0][1]["original"]["ficha"]), "los campos de la ficha no coinciden con el kit"


if __name__ == "__main__":
    main()
