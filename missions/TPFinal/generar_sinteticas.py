"""Genera conversaciones sintéticas reproducibles con el simulador oficial."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from admision.ejemplo import mensaje_de_sistema, primer_mensaje
from admision.entorno import Entorno
from admision.generador import generar


ROOT = Path(__file__).resolve().parent
VERSIONES_NORMAS = ("original", "b", "c")
SALIDA = ROOT / "curado" / "conversaciones_sinteticas.jsonl"
CONFIG = ROOT / "curado" / "sinteticas_config.json"
RESUMEN = ROOT / "curado" / "sinteticas_resumen.json"
SEMILLA = 20261108
CANTIDAD = 500


def normalizar(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or "").strip().lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def digitos(valor: str) -> str:
    return "".join(c for c in str(valor or "") if c.isdigit())


class Buscador:
    """Recuperador pequeño y determinista para dar evidencia normativa al generador."""

    k_entorno = 2

    def __init__(self, version: str):
        directorio = ROOT / "normas" / version
        self.normas = {
            p.stem: p.read_text(encoding="utf-8")
            for p in directorio.glob("NOR-*.md")
        }
        with (directorio / "parametros.yaml").open(encoding="utf-8") as archivo:
            self.parametros = {p["codigo"]: p for p in yaml.safe_load(archivo)["parametros"]}

    def recuperar(self, consulta: str, k: int) -> list[str]:
        q = normalizar(consulta)
        if "registro" in q or "documento" in q:
            seleccion = ["NOR-ADM-01", "NOR-ADM-02"] if "urgente" not in q else ["NOR-ADM-03", "NOR-ADM-01"]
        elif "circuito" in q or "sepsis" in q or "ecg" in q or "acv" in q:
            if "sepsis" in q:
                seleccion = ["NOR-TDE-03", "NOR-TDE-04"]
            elif "acv" in q:
                seleccion = ["NOR-TDE-02", "NOR-TDE-04"]
            elif "ecg" in q:
                seleccion = ["NOR-TDE-01", "NOR-TDE-04"]
            else:
                seleccion = ["NOR-TDE-01", "NOR-TDE-02"]
        elif "terminacion" in q or "reservado" in q or "inactiva" in q:
            seleccion = ["NOR-COB-03", "NOR-COB-04"]
        else:
            seleccion = ["NOR-COB-01", "NOR-COB-02"]
        fragmentos = []
        for codigo in seleccion[:k]:
            if codigo not in self.normas:
                continue
            texto = self.normas[codigo]
            usados = sorted(set(re.findall(r"\bP-[A-Z]+-\d+\b", texto)))
            valores = []
            for parametro in usados:
                dato = self.parametros.get(parametro)
                if not dato:
                    continue
                unidad = {"anios": "años", "dias": "días", "digito": "dígito"}.get(dato["unidad"], dato["unidad"])
                valores.append(f"{parametro} = {dato['valor']} {unidad}")
            if valores:
                texto += "\nValores: " + "; ".join(valores)
            fragmentos.append(texto)
        return fragmentos


def decidir(caso, params: dict[str, int]) -> dict[str, Any]:
    nivel = caso.nivel
    tiene_doc = bool(caso.documento_numero)
    registro = "provisorio" if not tiene_doc else "definitivo"
    if tiene_doc and caso.documento_tipo in {"pasaporte", "cédula"} and nivel <= params["P-ADM-3"]:
        registro = "provisorio"
    box_antes = nivel <= params["P-ADM-1"] or caso.edad >= params["P-ADM-2"]

    if caso.motivo == "dolor torácico":
        circuito, plazo = "ecg", params["P-TDE-1"]
    elif caso.motivo == "signos neurológicos focales de inicio súbito":
        circuito, plazo = "codigo_acv", params["P-TDE-2"]
    elif caso.sepsis != "no":
        circuito = "codigo_sepsis"
        plazo = params["P-TDE-3"] if caso.sepsis in {"probable", "con signos de shock"} else params["P-TDE-4"]
    else:
        circuito, plazo = "ninguno", None
    if circuito != "ninguno" and caso.llegada == "en ambulancia":
        plazo -= params["P-TDE-5"]

    entidad = None
    tipo = "sin_cobertura"
    afiliado = None
    if caso.trabajo:
        entidad, afiliado = caso.art
        tipo = "art"
    else:
        if caso.credenciales:
            preferidas = [c for c in caso.credenciales if c[0] == "prepaga"]
            cobertura = preferidas[0] if preferidas else caso.credenciales[0]
        else:
            cobertura = caso.declarada
        if cobertura:
            tipo_cobertura, entidad, afiliado = cobertura
            activa = caso.afiliaciones.get(f"{entidad}|{afiliado}", False)
            reservada = digitos(afiliado).endswith(str(params["P-COB-2"]))
            if reservada:
                tipo, entidad = "sin_cobertura", entidad
            elif activa:
                tipo = tipo_cobertura
            else:
                tipo, entidad = "sin_cobertura", None

    return {
        "registro": registro,
        "numero_documento": caso.documento_numero,
        "box_antes_del_registro": box_antes,
        "circuito": circuito,
        "plazo_circuito_min": plazo,
        "cobertura": tipo,
        "entidad_a_notificar": entidad,
        "aviso_al_voluntariado": caso.edad >= 76 and not caso.acompanante,
    }


def agregar_herramienta(mensajes: list[dict[str, str]], entorno: Entorno, herramienta: str, argumentos: dict[str, Any]) -> str:
    mensajes.append({
        "role": "assistant",
        "content": json.dumps({"herramienta": herramienta, "argumentos": argumentos}, ensure_ascii=False, separators=(",", ":")),
    })
    resultado, _ = entorno.paso(herramienta, argumentos)
    if herramienta != "registrar_decision":
        mensajes.append({"role": "user", "content": f"Resultado de {herramienta}:\n{resultado}"})
    return resultado


def main() -> None:
    casos = generar(semilla=SEMILLA, n=CANTIDAD, prefijo="sint")
    parametros_por_version = {}
    buscadores = {}
    for version in VERSIONES_NORMAS:
        with (ROOT / "normas" / version / "parametros.yaml").open(encoding="utf-8") as archivo:
            parametros_por_version[version] = {p["codigo"]: int(p["valor"]) for p in yaml.safe_load(archivo)["parametros"]}
        buscadores[version] = Buscador(version)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    circuitos = Counter()
    coberturas = Counter()
    conteo_versiones = Counter()

    with SALIDA.open("w", encoding="utf-8", newline="") as archivo:
        for indice, caso in enumerate(casos):
            version = VERSIONES_NORMAS[indice % len(VERSIONES_NORMAS)]
            params = parametros_por_version[version]
            buscador = buscadores[version]
            conteo_versiones[version] += 1
            entorno = Entorno(caso, buscador)
            mensajes = [
                {"role": "system", "content": mensaje_de_sistema()},
                {"role": "user", "content": primer_mensaje(caso.paciente_id)},
            ]
            agregar_herramienta(mensajes, entorno, "leer_triage", {"paciente_id": caso.paciente_id})
            agregar_herramienta(mensajes, entorno, "buscar_normativa", {"consulta": "registro documento box edad"})
            if caso.documento_tipo in {"pasaporte", "cédula"} and caso.nivel <= params["P-ADM-3"]:
                agregar_herramienta(mensajes, entorno, "buscar_normativa", {"consulta": "registro urgente pasaporte cédula"})
            circuito_query = "circuito sepsis" if caso.sepsis != "no" else (
                "circuito acv" if "neurológicos" in caso.motivo else "circuito ecg" if "torácico" in caso.motivo else "circuito tiempo"
            )
            agregar_herramienta(mensajes, entorno, "buscar_normativa", {"consulta": circuito_query})
            agregar_herramienta(mensajes, entorno, "buscar_normativa", {"consulta": "cobertura afiliación verificación ART"})
            agregar_herramienta(mensajes, entorno, "buscar_normativa", {"consulta": "cobertura sin cobertura terminación reservada"})

            quien = "paciente" if caso.puede_responder else "acompanante"
            if caso.trabajo:
                if not caso.credenciales and (caso.puede_responder or caso.acompanante):
                    agregar_herramienta(mensajes, entorno, "preguntar", {"paciente_id": caso.paciente_id, "a_quien": quien, "tema": "cobertura"})
                agregar_herramienta(mensajes, entorno, "preguntar", {"paciente_id": caso.paciente_id, "a_quien": quien, "tema": "art"})
            elif not caso.credenciales and (caso.puede_responder or caso.acompanante):
                agregar_herramienta(mensajes, entorno, "preguntar", {"paciente_id": caso.paciente_id, "a_quien": quien, "tema": "cobertura"})

            if caso.trabajo:
                entidad_verificada, numero_verificado = caso.art
                agregar_herramienta(mensajes, entorno, "verificar_afiliacion", {
                    "entidad": entidad_verificada, "numero_afiliado": numero_verificado,
                })
            else:
                if caso.credenciales:
                    prepagas = [c for c in caso.credenciales if c[0] == "prepaga"]
                    fuente = prepagas[0] if prepagas else caso.credenciales[0]
                else:
                    fuente = caso.declarada
                if fuente:
                    _, entidad_verificada, numero_verificado = fuente
                    agregar_herramienta(mensajes, entorno, "verificar_afiliacion", {
                        "entidad": entidad_verificada, "numero_afiliado": numero_verificado,
                    })

            decision = decidir(caso, params)
            agregar_herramienta(mensajes, entorno, "registrar_decision", decision)
            if entorno.decision is None:
                raise RuntimeError(f"El simulador no aceptó la decisión sintética {caso.id}.")
            ejemplo = {"id": caso.id, "normas": version, "messages": mensajes}
            archivo.write(json.dumps(ejemplo, ensure_ascii=False) + "\n")
            circuitos[decision["circuito"]] += 1
            coberturas[decision["cobertura"]] += 1

    CONFIG.write_text(json.dumps({
        "semilla": SEMILLA,
        "cantidad": CANTIDAD,
        "generador": "admision.generador.generar",
        "politica": "generar_sinteticas.py",
        "versiones_normas": list(VERSIONES_NORMAS),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    RESUMEN.write_text(json.dumps({
        "conversaciones_sinteticas": len(casos),
        "versiones_normas": dict(conteo_versiones),
        "circuitos": dict(circuitos),
        "coberturas": dict(coberturas),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if (ROOT / "curado" / "resumen.json").exists():
        resumen = json.loads((ROOT / "curado" / "resumen.json").read_text(encoding="utf-8"))
        resumen["sinteticas"] = len(casos)
        resumen["configuracion_sinteticas"] = "curado/sinteticas_config.json"
        (ROOT / "curado" / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generadas {len(casos)} conversaciones sintéticas con semilla {SEMILLA}: {SALIDA.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
