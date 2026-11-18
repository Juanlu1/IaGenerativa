"""Arma corridas/tabla.md con los resultados de todas las corridas de evaluar_todo.sh.

Lee corridas/<etiqueta>/<version>/resumen.json y tiempos.json (los escribe admision.correr) y pone, por etiqueta y
version de las normas, los casos resueltos, el tiempo y el contexto promedio por caso, al lado de la referencia de la
catedra (mission.md, "Como se corrige").

    uv run python tabla.py
"""

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CORRIDAS = RAIZ / "corridas"
VERSIONES = ("original", "b", "c")
# Referencia de la catedra sobre los 50 casos de practica (mission.md): Gemma 4 E4B sin entrenar y con SFT.
REFERENCIA = {"cátedra: sin entrenar": (12, 15, 12), "cátedra: SFT": (25, 24, 25)}
CASOS_REFERENCIA = 50


def leer(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def cargar() -> dict[str, dict[str, dict]]:
    corridas: dict[str, dict[str, dict]] = {}
    for resumen in sorted(CORRIDAS.glob("*/*/resumen.json")):
        carpeta = resumen.parent
        corridas.setdefault(carpeta.parent.name, {})[carpeta.name] = {
            "resumen": leer(resumen), "tiempos": leer(carpeta / "tiempos.json")}
    return corridas


def numero(valor, decimales: int = 0) -> str:
    if valor is None:
        return "-"
    return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tabla(corridas: dict[str, dict[str, dict]]) -> str:
    lineas = ["# Resultados de las corridas", "",
              "Generado por `uv run python tabla.py` a partir de `corridas/<etiqueta>/<version>/`. No editar a mano.", "",
              "## Casos resueltos", "",
              "| Etiqueta | " + " | ".join(VERSIONES) + " |", "|---|" + "---:|" * len(VERSIONES)]
    for etiqueta, (o, b, c) in REFERENCIA.items():
        lineas.append(f"| {etiqueta} | " + " | ".join(f"{n}/{CASOS_REFERENCIA}" for n in (o, b, c)) + " |")
    for etiqueta, por_version in corridas.items():
        celdas = []
        for version in VERSIONES:
            r = por_version.get(version, {}).get("resumen")
            celdas.append(f"{r['resueltos']}/{r['casos']}" if r else "-")
        lineas.append(f"| {etiqueta} | " + " | ".join(celdas) + " |")

    lineas += ["", "## Detalle por corrida", "",
               "- Segundos por caso: `jugar_lote` entero dividido por la cantidad de casos (los casos corren en lote).",
               "- Contexto por caso: caracteres que se le pasaron al modelo en todo el caso, según `admision.correr`.",
               "",
               "| Etiqueta | Versión | Resueltos | Parcial medio | Sin ficha | Búsquedas por caso "
               "| Segundos por caso | Contexto por caso (caracteres) | construir_agente (s) | Error |",
               "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for etiqueta, por_version in corridas.items():
        for version in sorted(por_version, key=lambda v: (VERSIONES + (v,)).index(v)):
            r, t = por_version[version]["resumen"], por_version[version]["tiempos"]
            error = r.get("error") or t.get("error")
            lineas.append(" | ".join([
                f"| {etiqueta}", version, f"{r['resueltos']}/{r['casos']}", numero(r.get("parcial_medio"), 3),
                str(r.get("sin_decision", "-")), numero(r.get("busquedas_por_caso"), 2),
                numero(t.get("jugar_lote_por_caso"), 3), numero(r.get("caracteres_de_contexto_por_caso")),
                numero(t.get("construir_agente"), 1), (str(error).replace("|", "/") if error else "")]) + " |")
    return "\n".join(lineas) + "\n"


def main() -> None:
    corridas = cargar()
    salida = CORRIDAS / "tabla.md"
    salida.parent.mkdir(exist_ok=True)
    salida.write_text(tabla(corridas), encoding="utf-8")
    print(f"{salida.relative_to(RAIZ)}: {sum(len(v) for v in corridas.values())} corridas de {len(corridas)} etiquetas")


if __name__ == "__main__":
    main()
