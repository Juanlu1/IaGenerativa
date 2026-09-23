"""Parte 1: grilla de experimentos del recuperador, medidos con el evaluador oficial.

    python3 experimentar.py [--encoders bert-base minilm ...]

Por cada configuración escribe experimentos/<nombre>.jsonl, corre
evaluar/evaluar.py (que deja <nombre>.jsonl.eval.json al lado) y al final arma
experimentos/tabla.md, ordenada por context_relevance.
"""
import argparse
import json
import subprocess
import sys

from recuperador import ENCODERS, RAIZ, Recuperador, crear_encoder, leer_corpus
from recuperar import procesar

PREGUNTAS = RAIZ / "datos" / "preguntas_recuperacion_dev.jsonl"
SALIDA = RAIZ / "experimentos"

CHUNKINGS = [
    {"chunking": "seccion", "metadatos": False, "tam_ventana": None, "solapamiento": None},
    {"chunking": "seccion", "metadatos": True, "tam_ventana": None, "solapamiento": None},
    {"chunking": "ventana", "metadatos": False, "tam_ventana": 40, "solapamiento": 10},
    {"chunking": "ventana", "metadatos": False, "tam_ventana": 80, "solapamiento": 20},
]

SELECCIONES = [
    {"k": 1, "umbral": None, "margen": None},
    {"k": 3, "umbral": None, "margen": None},
    {"k": 5, "umbral": None, "margen": None},
    {"k": 3, "umbral": None, "margen": 0.02},
    {"k": 3, "umbral": None, "margen": 0.05},
]


def nombre(cfg):
    if cfg["chunking"] == "seccion":
        chunk = "seccion-meta" if cfg["metadatos"] else "seccion"
    else:
        chunk = f"ventana{cfg['tam_ventana']}-{cfg['solapamiento']}"
    sel = f"k{cfg['k']}"
    if cfg["umbral"] is not None:
        sel += f"-u{cfg['umbral']}"
    if cfg["margen"] is not None:
        sel += f"-m{cfg['margen']}"
    return f"{cfg['encoder']}__{chunk}__{sel}"


def evaluar(cfg, recuperador):
    salida = SALIDA / f"{nombre(cfg)}.jsonl"
    procesar(PREGUNTAS, salida, recuperador)
    subprocess.run([sys.executable, str(RAIZ / "evaluar" / "evaluar.py"), "recuperacion",
                    "--preguntas", str(PREGUNTAS), "--resultados", str(salida)],
                   check=True, capture_output=True)
    return json.loads(salida.with_name(salida.name + ".eval.json").read_text(encoding="utf-8"))["resumen"]


def fila_tabla(cfg, r):
    chunk = "sección" if cfg["chunking"] == "seccion" else f"ventana {cfg['tam_ventana']}/{cfg['solapamiento']}"
    fmt = lambda v: "—" if v is None else v
    return (f"| {cfg['encoder']} | {chunk} | {'sí' if cfg['metadatos'] else 'no'} | {cfg['k']} | "
            f"{fmt(cfg['umbral'])} | {fmt(cfg['margen'])} | **{r['context_relevance']:.3f}** | "
            f"{r['recall']:.3f} | {r['precision']:.3f} | {r['mrr']:.3f} | {r['k']:.2f} | "
            f"`{nombre(cfg)}.jsonl.eval.json` |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--encoders", nargs="+", default=list(ENCODERS), choices=list(ENCODERS))
    args = ap.parse_args()
    SALIDA.mkdir(exist_ok=True)
    corpus = leer_corpus()
    for enc in args.encoders:
        print(f"== {enc}", flush=True)
        encoder = crear_encoder(enc)  # un modelo cargado por encoder, reutilizado en toda la grilla
        for chunk in CHUNKINGS:
            rec = Recuperador({"encoder": enc, **chunk, **SELECCIONES[0]}, encoder=encoder, corpus=corpus)
            for sel in SELECCIONES:
                rec.cfg = {"encoder": enc, **chunk, **sel}
                r = evaluar(rec.cfg, rec)
                print(f"  {nombre(rec.cfg):45s} CR {r['context_relevance']:.3f}", flush=True)
    escribir_tabla()


def escribir_tabla():
    """Arma tabla.md a partir de todos los .eval.json de experimentos/, así una
    corrida parcial (--encoders) no borra las filas de las anteriores."""
    filas = []
    for ev in SALIDA.glob("*.jsonl.eval.json"):
        enc, chunk, sel = ev.name.removesuffix(".jsonl.eval.json").split("__")
        cfg = {"encoder": enc, "metadatos": chunk == "seccion-meta", "umbral": None, "margen": None}
        if chunk.startswith("ventana"):
            tam, sol = chunk.removeprefix("ventana").split("-")
            cfg.update(chunking="ventana", tam_ventana=int(tam), solapamiento=int(sol))
        else:
            cfg.update(chunking="seccion", tam_ventana=None, solapamiento=None)
        for parte in sel.split("-"):
            if parte[0] == "k":
                cfg["k"] = int(parte[1:])
            elif parte[0] == "u":
                cfg["umbral"] = float(parte[1:])
            elif parte[0] == "m":
                cfg["margen"] = float(parte[1:])
        filas.append((cfg, json.loads(ev.read_text(encoding="utf-8"))["resumen"]))
    filas.sort(key=lambda f: -f[1]["context_relevance"])
    encabezado = ("| Encoder | Chunking | Metadatos | k | Umbral | Margen | Context relevance | Recall | "
                  "Precision | MRR | Fragmentos prom. | Evaluación |\n|" + "---|" * 12 + "\n")
    (SALIDA / "tabla.md").write_text(
        "# Experimentos de la parte 1\n\nGenerada por `experimentar.py` con `evaluar/evaluar.py` "
        f"sobre `datos/preguntas_recuperacion_dev.jsonl`. {len(filas)} configuraciones, "
        "ordenadas por context relevance.\n\n" + encabezado
        + "\n".join(fila_tabla(c, r) for c, r in filas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
