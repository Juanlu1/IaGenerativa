"""Genera conversaciones sintéticas reproducibles con el simulador oficial.

Cada caso sale de `admision.generador.generar` y lo juega una política determinista
derivada de las normas y de las costumbres del historial. Las búsquedas pasan por
el buscador del grupo (`parte2/rag_buscador.py`) armado con la carpeta de normas de
la versión que le toca al caso, así que cada conversación muestra los números de
esa versión. Las consultas siguen las mismas plantillas que usan las trazas de la
cátedra (`entrenamiento/trazas.jsonl`), que son las que va a escribir el agente.

La misma política se valida contra las fichas esperadas de `practica/` con
`validar_politica.py`.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from admision.casos import Caso
from admision.ejemplo import mensaje_de_sistema, primer_mensaje
from admision.entorno import Entorno
from admision.generador import generar
from admision.normas import cargar_normas
from parte2.rag_buscador import construir_buscador

import yaml

ROOT = Path(__file__).resolve().parent
VERSIONES_NORMAS = ("original", "b", "c")
SALIDA = ROOT / "curado" / "conversaciones_sinteticas.jsonl"
CONFIG = ROOT / "curado" / "sinteticas_config.json"
RESUMEN = ROOT / "curado" / "sinteticas_resumen.json"
SEMILLA = 20261108
CANTIDAD = 600

# Costumbre del historial (costumbres.md): aviso al voluntariado para 75 años o más sin acompañante.
# Es el mismo corte que curar.py (EDAD_VOLUNTARIADO); ver revision_parte1.md.
EDAD_VOLUNTARIADO = 75

# Plantillas de consulta: son las 14 que aparecen en las trazas de la cátedra.
CONSULTA_REGISTRO = "registro del paciente y ubicación en el box"
CONSULTA_PASAPORTE = "registro con pasaporte o cédula"
CONSULTA_AMBULANCIA = "ingreso en ambulancia plazo del circuito"
CONSULTA_RESERVADA = "número de afiliado con terminación reservada"
CONSULTA_VERIFICACION = "consulta y verificación de la cobertura"
CONSULTA_SIN_CREDENCIAL = "consulta de la cobertura sin credencial"
CONSULTA_ART = "accidente de trabajo ART"
CONSULTA_CIRCUITO = {
    "ecg": "dolor torácico plazo",
    "codigo_acv": "signos neurológicos focales de inicio súbito plazo",
    "codigo_sepsis": "código sepsis plazo",
}


def digitos(valor: str | None) -> str:
    return "".join(c for c in str(valor or "") if c.isdigit())


def cargar_parametros(version_o_ruta: str | Path) -> dict[str, int]:
    ruta = Path(version_o_ruta)
    if not ruta.is_dir():
        ruta = ROOT / "normas" / str(version_o_ruta)
    datos = yaml.safe_load((ruta / "parametros.yaml").read_text(encoding="utf-8"))
    return {p["codigo"]: int(p["valor"]) for p in datos["parametros"]}


def circuito_del_caso(caso: Caso) -> str:
    if caso.motivo == "dolor torácico":
        return "ecg"
    if caso.motivo == "signos neurológicos focales de inicio súbito":
        return "codigo_acv"
    if caso.sepsis != "no":
        return "codigo_sepsis"
    return "ninguno"


def cobertura_a_verificar(caso: Caso) -> tuple[str, str, str] | None:
    """(tipo, entidad, número) de la obra social o prepaga que corresponde verificar, fuera de la ART.

    Con dos credenciales se elige la prepaga (costumbre del historial). Sin credencial,
    vale lo que declara el paciente o su acompañante; si no puede responder nadie, None.
    """
    if caso.credenciales:
        prepagas = [c for c in caso.credenciales if c[0] == "prepaga"]
        return prepagas[0] if prepagas else caso.credenciales[0]
    if caso.puede_responder or caso.acompanante:
        return caso.declarada
    return None


def decidir(caso: Caso, params: dict[str, int], activa: bool | None) -> dict[str, Any]:
    """La ficha según las normas y las costumbres. `activa` es lo que informó la verificación."""
    nivel = caso.nivel
    tiene_doc = bool(caso.documento_numero)
    registro = "definitivo" if tiene_doc else "provisorio"
    if tiene_doc and caso.documento_tipo in {"pasaporte", "cédula"} and nivel <= params["P-ADM-3"]:
        registro = "provisorio"  # NOR-ADM-03
    box_antes = nivel <= params["P-ADM-1"] or caso.edad >= params["P-ADM-2"]  # NOR-ADM-01 §4, NOR-ADM-02

    circuito = circuito_del_caso(caso)
    plazo = {
        "ecg": params["P-TDE-1"],
        "codigo_acv": params["P-TDE-2"],
        "codigo_sepsis": params["P-TDE-3"] if caso.sepsis in {"probable", "con signos de shock"} else params["P-TDE-4"],
    }.get(circuito)
    if plazo is not None and caso.llegada == "en ambulancia":
        plazo -= params["P-TDE-5"]  # NOR-TDE-04

    if caso.trabajo:  # NOR-COB-02 §5: cubre la ART
        tipo, entidad = "art", caso.art[0]
    else:
        fuente = cobertura_a_verificar(caso)
        if fuente is None:
            tipo, entidad = "sin_cobertura", None
        elif digitos(fuente[2]).endswith(str(params["P-COB-2"])):
            tipo, entidad = "sin_cobertura", fuente[1]  # NOR-COB-04: sin cobertura, pero se notifica
        elif activa:
            tipo, entidad = fuente[0], fuente[1]
        else:
            tipo, entidad = "sin_cobertura", None  # NOR-COB-03 §4

    return {
        "registro": registro,
        "numero_documento": caso.documento_numero,
        "box_antes_del_registro": box_antes,
        "circuito": circuito,
        "plazo_circuito_min": plazo,
        "cobertura": tipo,
        "entidad_a_notificar": entidad,
        "aviso_al_voluntariado": caso.edad >= EDAD_VOLUNTARIADO and not caso.acompanante,
    }


def consulta_del_tema(caso: Caso) -> str:
    """La consulta de cobertura y circuito, con la misma composición que las trazas de la cátedra."""
    circuito = circuito_del_caso(caso)
    if caso.trabajo:
        prefijo = CONSULTA_ART
    elif not caso.credenciales:
        prefijo = CONSULTA_SIN_CREDENCIAL
    else:
        prefijo = ""
    sufijo = CONSULTA_CIRCUITO.get(circuito, "")
    return f"{prefijo} {sufijo}".strip() or CONSULTA_VERIFICACION


def jugar_caso(caso: Caso, buscador, params: dict[str, int],
               sistema: str | None = None) -> tuple[list[dict[str, str]], Entorno]:
    """Juega un caso con la política y devuelve la conversación y el entorno (con su log y su ficha)."""
    entorno = Entorno(caso, buscador)
    mensajes = [
        {"role": "system", "content": sistema if sistema is not None else mensaje_de_sistema()},
        {"role": "user", "content": primer_mensaje(caso.paciente_id)},
    ]

    def paso(herramienta: str, argumentos: dict[str, Any]) -> str:
        mensajes.append({"role": "assistant", "content": json.dumps(
            {"herramienta": herramienta, "argumentos": argumentos}, ensure_ascii=False, separators=(",", ":"))})
        resultado, _ = entorno.paso(herramienta, argumentos)
        if herramienta != "registrar_decision":
            mensajes.append({"role": "user", "content": f"Resultado de {herramienta}:\n{resultado}"})
        return resultado

    pid = caso.paciente_id
    paso("leer_triage", {"paciente_id": pid})
    paso("buscar_normativa", {"consulta": CONSULTA_REGISTRO})
    if caso.documento_tipo in {"pasaporte", "cédula"}:
        paso("buscar_normativa", {"consulta": CONSULTA_PASAPORTE})
    paso("buscar_normativa", {"consulta": consulta_del_tema(caso)})
    if caso.llegada == "en ambulancia" and circuito_del_caso(caso) != "ninguno":
        paso("buscar_normativa", {"consulta": CONSULTA_AMBULANCIA})

    quien = "paciente" if caso.puede_responder else ("acompanante" if caso.acompanante else None)
    if not caso.credenciales and quien:
        paso("preguntar", {"paciente_id": pid, "a_quien": quien, "tema": "cobertura"})
    if caso.trabajo and quien:
        paso("preguntar", {"paciente_id": pid, "a_quien": quien, "tema": "art"})

    activa = None
    if caso.trabajo:
        entidad, numero = caso.art
        paso("verificar_afiliacion", {"entidad": entidad, "numero_afiliado": numero})
    else:
        fuente = cobertura_a_verificar(caso)
        if fuente is not None:
            paso("buscar_normativa", {"consulta": CONSULTA_RESERVADA})
            resultado = paso("verificar_afiliacion", {"entidad": fuente[1], "numero_afiliado": fuente[2]})
            activa = "activa" in resultado and "inactiva" not in resultado

    ficha = decidir(caso, params, activa)
    ficha["fundamentos"] = fundamentos(caso, ficha, params)
    paso("registrar_decision", ficha)
    return mensajes, entorno


def fundamentos(caso: Caso, ficha: dict[str, Any], params: dict[str, int]) -> list[str]:
    """Secciones que justifican la ficha (optativo en el contrato; no se corrige)."""
    secciones = ["NOR-ADM-01"]
    if caso.edad >= params["P-ADM-2"]:
        secciones.append("NOR-ADM-02")
    if caso.documento_tipo in {"pasaporte", "cédula"}:
        secciones.append("NOR-ADM-03")
    secciones.append("NOR-COB-01")
    if ficha["cobertura"] in {"obra_social", "prepaga", "art"}:
        secciones.append("NOR-COB-02")
    if ficha["cobertura"] == "sin_cobertura":
        secciones.append("NOR-COB-03")
    if ficha["cobertura"] == "sin_cobertura" and ficha["entidad_a_notificar"]:
        secciones.append("NOR-COB-04")
    seccion_circuito = {"ecg": "NOR-TDE-01", "codigo_acv": "NOR-TDE-02", "codigo_sepsis": "NOR-TDE-03"}
    if ficha["circuito"] in seccion_circuito:
        secciones.append(seccion_circuito[ficha["circuito"]])
        if caso.llegada == "en ambulancia":
            secciones.append("NOR-TDE-04")
    return secciones


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--semilla", type=int, default=SEMILLA)
    parser.add_argument("--cantidad", type=int, default=CANTIDAD)
    parser.add_argument("--salida", type=Path, default=SALIDA)
    args = parser.parse_args()

    casos = generar(semilla=args.semilla, n=args.cantidad, prefijo="sint")
    parametros = {v: cargar_parametros(v) for v in VERSIONES_NORMAS}
    buscadores = {v: construir_buscador(ROOT / "normas" / v) for v in VERSIONES_NORMAS}
    for v in VERSIONES_NORMAS:  # la carpeta tiene que cargar con el cargador oficial
        cargar_normas(ROOT / "normas" / v)

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    circuitos, coberturas, versiones, consultas = Counter(), Counter(), Counter(), Counter()
    with args.salida.open("w", encoding="utf-8", newline="") as archivo:
        for indice, caso in enumerate(casos):
            # Reparto en rueda: cada versión de normas recibe un tercio de los casos.
            version = VERSIONES_NORMAS[indice % len(VERSIONES_NORMAS)]
            mensajes, entorno = jugar_caso(caso, buscadores[version], parametros[version])
            if entorno.decision is None or any(not e["valida"] for e in entorno.log):
                raise RuntimeError(f"El simulador rechazó un paso del caso sintético {caso.id}.")
            versiones[version] += 1
            circuitos[entorno.decision["circuito"]] += 1
            coberturas[entorno.decision["cobertura"]] += 1
            consultas.update(e["argumentos"]["consulta"] for e in entorno.log if e["herramienta"] == "buscar_normativa")
            archivo.write(json.dumps({"id": caso.id, "normas": version, "messages": mensajes},
                                     ensure_ascii=False) + "\n")

    CONFIG.write_text(json.dumps({
        "semilla": args.semilla,
        "cantidad": args.cantidad,
        "generador": "admision.generador.generar",
        "politica": "generar_sinteticas.py (decidir y jugar_caso)",
        "buscador": "parte2/rag_buscador.py (construir_buscador sobre normas/<version>)",
        "versiones_normas": list(VERSIONES_NORMAS),
        "reparto": "en rueda por indice de caso",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    RESUMEN.write_text(json.dumps({
        "conversaciones_sinteticas": len(casos),
        "versiones_normas": dict(versiones),
        "circuitos": dict(circuitos),
        "coberturas": dict(coberturas),
        "consultas": dict(consultas.most_common()),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    resumen_curado = ROOT / "curado" / "resumen.json"
    if resumen_curado.exists():
        resumen = json.loads(resumen_curado.read_text(encoding="utf-8"))
        resumen["sinteticas"] = len(casos)
        resumen["configuracion_sinteticas"] = "curado/sinteticas_config.json"
        resumen_curado.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generadas {len(casos)} conversaciones sintéticas con semilla {args.semilla}: {args.salida}")


if __name__ == "__main__":
    main()
