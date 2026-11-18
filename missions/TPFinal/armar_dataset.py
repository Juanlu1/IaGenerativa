"""Arma el conjunto de entrenamiento de la Parte 4 (SFT) en `datos/`.

Junta tres orígenes, todos en el formato de conversación del README del kit
(mensaje de sistema, primer mensaje del usuario, una llamada JSON por turno del
asistente y `Resultado de <herramienta>:` como turno del usuario):

  historial     trazas de `historial/trazas.jsonl` cuyas filas quedaron `correcta`
                en `historial_clasificado.csv` (normas originales);
  catedra       las 800 trazas de `entrenamiento/trazas.jsonl` (cada una con sus
                propios valores de las normas);
  sinteticas    `curado/conversaciones_sinteticas.jsonl` (normas original, b y c).

Búsquedas con los números de cada traza
--------------------------------------
Las búsquedas de las trazas se vuelven a hacer con el buscador del grupo
(`parte2/rag_buscador.py`), para que el modelo vea en el entrenamiento lo mismo
que va a ver en operación. Los textos de las normas son iguales en las tres
versiones; solo cambia `parametros.yaml`. Por eso, para cada traza:

  1. se leen los valores que muestran sus propios resultados de
     `buscar_normativa` («Valores: P-ADM-2 = 60 años; ...»);
  2. se arma una carpeta temporal de normas con los textos de `normas/original`
     y un `parametros.yaml` con esos valores; los parámetros que no cambian entre
     versiones (P-COB-1 y los de otras áreas) se toman de `normas/original`;
  3. se corre el buscador del grupo sobre esa carpeta con la consulta de la traza.

Si el resultado nuevo cita un parámetro que varía entre versiones y que la
traza nunca mostró, su valor es desconocido: esa búsqueda conserva el resultado
original de la traza (que ya tiene los números correctos) y se cuenta en
`datos/resumen.json`. Además se controla que, cuando el buscador devuelve las
mismas secciones que la traza, el texto coincide carácter por carácter.

Uso:
    uv run python armar_dataset.py --prompt prompt_optimizado.txt
    uv run python armar_dataset.py            # mensaje de sistema de admision/ejemplo.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

from admision.ejemplo import mensaje_de_sistema, primer_mensaje
from admision.entorno import K_POR_DEFECTO
from admision.normas import PATRON_PARAMETRO
from parte2.rag_buscador import construir_buscador

ROOT = Path(__file__).resolve().parent
NORMAS = ROOT / "normas"
SEMILLA = 20261117
FRACCION_VAL = 0.05
LIMITE_GIT_MB = 50
CARACTERES_POR_TOKEN = 4  # la misma estimación que usa admision.evaluar_rag

_SECCION = re.compile(r"^## (NOR-[A-Z]{3}-\d{2})", re.MULTILINE)


# ---------------------------------------------------------------- utilidades

def leer_jsonl(ruta: Path) -> list[dict[str, Any]]:
    with ruta.open(encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def llamada(herramienta: str, argumentos: Any) -> str:
    """Formato canónico del turno del asistente: JSON compacto, sin texto alrededor."""
    return json.dumps({"herramienta": herramienta, "argumentos": argumentos},
                      ensure_ascii=False, separators=(",", ":"))


def parametros_yaml(ruta: Path) -> list[dict[str, Any]]:
    return yaml.safe_load((ruta / "parametros.yaml").read_text(encoding="utf-8"))["parametros"]


def parametros_variables() -> set[str]:
    """Parámetros cuyo valor cambia entre normas/original, b y c (los demás son fijos)."""
    versiones = [{p["codigo"]: p["valor"] for p in parametros_yaml(NORMAS / v)} for v in ("original", "b", "c")]
    return {k for k in versiones[0] if len({v[k] for v in versiones}) > 1}


def entero(texto: str) -> int:
    numero = re.search(r"-?\d+", texto)
    if not numero:
        raise ValueError(f"valor sin número: {texto!r}")
    return int(numero.group())


def citados(texto: str) -> set[str]:
    return {f"{p}-{n}" for p, desde, hasta in PATRON_PARAMETRO.findall(texto)
            for n in range(int(desde), int(hasta or desde) + 1)}


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


# --------------------------------------------- búsquedas con los valores de la traza

class Rebuscador:
    """Rehace las búsquedas de una traza con el buscador del grupo y los valores de esa traza."""

    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.base = parametros_yaml(NORMAS / "original")
        self.variables = parametros_variables()
        self.textos = sorted((NORMAS / "original").glob("NOR-*.md"))
        self._buscadores: dict[tuple, Any] = {}
        self.stats = Counter(busquedas=0, busquedas_mismas_secciones=0, busquedas_con_resultado_original=0)

    def valores_de(self, traza: dict[str, Any]) -> dict[str, int]:
        valores: dict[str, int] = {}
        for paso in traza["pasos"]:
            if paso["herramienta"] != "buscar_normativa":
                continue
            for linea in str(paso["resultado"]).splitlines():
                if not linea.startswith("Valores: "):
                    continue
                # «Valores: P-TDE-3 = 15 min; P-TDE-4 = 60 min.» (admision.normas.linea_de_valores)
                for par in linea[len("Valores: "):].rstrip(".").split("; "):
                    codigo, _, texto = par.partition(" = ")
                    v = entero(texto)
                    if valores.setdefault(codigo, v) != v:
                        raise ValueError(f"{traza['id']}: {codigo} muestra dos valores distintos")
        return valores

    def buscador(self, valores: dict[str, int]):
        clave = tuple(sorted(valores.items()))
        if clave not in self._buscadores:
            carpeta = self.tmp / f"normas_{len(self._buscadores):04d}"
            carpeta.mkdir()
            for archivo in self.textos:
                shutil.copy(archivo, carpeta / archivo.name)
            parametros = [dict(p, valor=valores.get(p["codigo"], p["valor"])) for p in self.base]
            (carpeta / "parametros.yaml").write_text(
                yaml.safe_dump({"parametros": parametros}, allow_unicode=True, sort_keys=False), encoding="utf-8")
            self._buscadores[clave] = construir_buscador(carpeta)
        return self._buscadores[clave]

    def rehacer(self, traza: dict[str, Any]) -> list[str]:
        """Devuelve, por paso, el resultado a mostrar (nuevo o el original si no se puede)."""
        valores = self.valores_de(traza)
        conocidos = set(valores) | (set(p["codigo"] for p in self.base) - self.variables)
        buscador = self.buscador(valores)
        k = getattr(buscador, "k_entorno", K_POR_DEFECTO)
        resultados = []
        for paso in traza["pasos"]:
            original = str(paso["resultado"])
            if paso["herramienta"] != "buscar_normativa":
                resultados.append(original)
                continue
            fragmentos = buscador.recuperar(str(paso["argumentos"]["consulta"]), k)
            nuevo = "\n\n".join(f if isinstance(f, str) else f.texto for f in fragmentos)
            self.stats["busquedas"] += 1
            if citados(nuevo) - conocidos:
                self.stats["busquedas_con_resultado_original"] += 1
                resultados.append(original)
                continue
            if _SECCION.findall(nuevo) == _SECCION.findall(original):
                self.stats["busquedas_mismas_secciones"] += 1
                if nuevo != original:
                    raise ValueError(f"{traza['id']}: mismas secciones con distinto texto; revisar los valores")
            resultados.append(nuevo)
        return resultados


# ------------------------------------------------------------------ orígenes

def conversacion_de_traza(traza: dict[str, Any], resultados: list[str], sistema: str) -> list[dict[str, str]]:
    mensajes = [{"role": "system", "content": sistema},
                {"role": "user", "content": primer_mensaje(traza["paciente_id"])}]
    for paso, resultado in zip(traza["pasos"], resultados, strict=True):
        mensajes.append({"role": "assistant", "content": llamada(paso["herramienta"], paso["argumentos"])})
        if paso["herramienta"] != "registrar_decision":
            mensajes.append({"role": "user", "content": f"Resultado de {paso['herramienta']}:\n{resultado}"})
    return mensajes


def desde_trazas(ruta: Path, origen: str, sistema: str, rebuscador: Rebuscador | None,
                 ids: set[str] | None = None) -> list[dict[str, Any]]:
    ejemplos = []
    for traza in leer_jsonl(ruta):
        if ids is not None and traza["id"] not in ids:
            continue
        if not traza["pasos"] or traza["pasos"][-1]["herramienta"] != "registrar_decision":
            raise ValueError(f"{traza['id']}: la traza no termina en registrar_decision")
        resultados = rebuscador.rehacer(traza) if rebuscador else [str(p["resultado"]) for p in traza["pasos"]]
        ejemplos.append({"id": traza["id"], "origen": origen,
                         "messages": conversacion_de_traza(traza, resultados, sistema)})
    return ejemplos


def desde_sinteticas(ruta: Path, sistema: str) -> list[dict[str, Any]]:
    ejemplos = []
    for fila in leer_jsonl(ruta):
        mensajes = [dict(m) for m in fila["messages"]]
        if mensajes[0]["role"] != "system":
            raise ValueError(f"{fila['id']}: falta el mensaje de sistema")
        mensajes[0]["content"] = sistema
        for m in mensajes:
            if m["role"] == "assistant":
                obj = json.loads(m["content"])
                m["content"] = llamada(obj["herramienta"], obj["argumentos"])
        ejemplos.append({"id": fila["id"], "origen": "sinteticas", "normas": fila.get("normas"),
                         "messages": mensajes})
    return ejemplos


# ---------------------------------------------------------------- tokens

def contador_de_tokens(nombre: str | None):
    if not nombre:
        return (lambda mensajes: sum(len(m["content"]) for m in mensajes) // CARACTERES_POR_TOKEN,
                f"estimacion: caracteres de los mensajes / {CARACTERES_POR_TOKEN}, como admision.evaluar_rag")
    from transformers import AutoTokenizer  # solo si se pide; en Lightning, con el tokenizador real
    tok = AutoTokenizer.from_pretrained(nombre)
    # Igual que entrenar.py: se renderiza la plantilla y se tokeniza el texto (en transformers 5,
    # apply_chat_template(tokenize=True) devuelve un diccionario, no la lista de ids).
    return (lambda mensajes: len(tok(tok.apply_chat_template(mensajes, tokenize=False),
                                     add_special_tokens=False)["input_ids"]),
            f"apply_chat_template de {nombre}")


# ------------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prompt", type=Path, help="archivo con el mensaje de sistema (por defecto, el de admision/ejemplo.py)")
    parser.add_argument("--salida", type=Path, default=ROOT / "datos")
    parser.add_argument("--semilla", type=int, default=SEMILLA)
    parser.add_argument("--val", type=float, default=FRACCION_VAL, help="fracción de validación por origen")
    parser.add_argument("--origenes", default="historial,catedra,sinteticas")
    parser.add_argument("--busquedas", choices=["buscador", "originales"], default="buscador",
                        help="rehacer las búsquedas con el buscador del grupo o dejar las de la traza")
    parser.add_argument("--tokenizador", help="id de Hugging Face para contar tokens exactos (por defecto, estimación)")
    parser.add_argument("--subir-hf", metavar="REPO", help="sube train/val/resumen a ese repo de dataset de Hugging Face")
    args = parser.parse_args()

    sistema = args.prompt.read_text(encoding="utf-8").strip() if args.prompt else mensaje_de_sistema()
    origenes = [o.strip() for o in args.origenes.split(",") if o.strip()]

    with tempfile.TemporaryDirectory() as tmp:
        rebuscador = Rebuscador(Path(tmp)) if args.busquedas == "buscador" else None
        ejemplos: list[dict[str, Any]] = []
        if "historial" in origenes:
            with (ROOT / "historial_clasificado.csv").open(encoding="utf-8") as f:
                correctas = {r["id"] for r in csv.DictReader(f) if r["tipo"] == "correcta"}
            ejemplos += desde_trazas(ROOT / "historial" / "trazas.jsonl", "historial", sistema, rebuscador, correctas)
        if "catedra" in origenes:
            ejemplos += desde_trazas(ROOT / "entrenamiento" / "trazas.jsonl", "catedra", sistema, rebuscador)
        if "sinteticas" in origenes:
            ejemplos += desde_sinteticas(ROOT / "curado" / "conversaciones_sinteticas.jsonl", sistema)
        stats_busquedas = dict(rebuscador.stats) if rebuscador else {}

    # Separación por origen, con semilla fija: cada origen aporta ~5% a validación.
    rng = random.Random(args.semilla)
    por_origen: dict[str, list] = defaultdict(list)
    for e in ejemplos:
        por_origen[e["origen"]].append(e)
    train, val = [], []
    for origen in sorted(por_origen):
        grupo = por_origen[origen]
        rng.shuffle(grupo)
        n_val = round(len(grupo) * args.val)
        val += grupo[:n_val]
        train += grupo[n_val:]
    rng.shuffle(train)
    rng.shuffle(val)

    args.salida.mkdir(parents=True, exist_ok=True)
    rutas = {"train": args.salida / "train.jsonl", "val": args.salida / "val.jsonl"}
    for nombre, filas in (("train", train), ("val", val)):
        with rutas[nombre].open("w", encoding="utf-8", newline="\n") as f:
            f.writelines(json.dumps(e, ensure_ascii=False) + "\n" for e in filas)

    contar, metodo = contador_de_tokens(args.tokenizador)
    tokens = {id(e): contar(e["messages"]) for e in ejemplos}
    largos = sorted(tokens.values())
    mayor = max(ejemplos, key=lambda e: tokens[id(e)])
    peso_train_mb = rutas["train"].stat().st_size / 2**20
    resumen = {
        "semilla": args.semilla,
        "prompt": str(args.prompt) if args.prompt else "admision/ejemplo.py:mensaje_de_sistema()",
        "busquedas": args.busquedas,
        "conversaciones": len(ejemplos),
        "conversaciones_por_origen": {o: len(g) for o, g in sorted(por_origen.items())},
        "train_por_origen": dict(sorted(Counter(e["origen"] for e in train).items())),
        "val_por_origen": dict(sorted(Counter(e["origen"] for e in val).items())),
        "sinteticas_por_normas": dict(sorted(Counter(e["normas"] for e in ejemplos if e["origen"] == "sinteticas").items())),
        "metodo_tokens": metodo,
        "tokens_totales": sum(largos),
        "tokens_train": sum(tokens[id(e)] for e in train),
        "tokens_val": sum(tokens[id(e)] for e in val),
        "tokens_por_conversacion": {"medio": round(sum(largos) / len(largos), 1),
                                    "p50": largos[len(largos) // 2],
                                    "p95": largos[int(len(largos) * 0.95)],
                                    "maximo": largos[-1], "conversacion_mas_larga": mayor["id"]},
        "tokens_mensaje_de_sistema": contar([{"role": "system", "content": sistema}]),
        "busquedas_rehechas": stats_busquedas,
        "archivos": {n: {"ruta": str(r.relative_to(ROOT)) if r.is_relative_to(ROOT) else str(r),
                         "lineas": len(train if n == "train" else val), "sha256": sha256(r),
                         "mb": round(r.stat().st_size / 2**20, 2)} for n, r in rutas.items()},
        "limite_git_mb": LIMITE_GIT_MB,
        "train_va_a_git": peso_train_mb <= LIMITE_GIT_MB,
    }
    (args.salida / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))

    if peso_train_mb > LIMITE_GIT_MB:
        print(f"\ntrain.jsonl pesa {peso_train_mb:.1f} MB (> {LIMITE_GIT_MB} MB): no lo commitees; "
              "subilo con --subir-hf <usuario>/<repo> (ver modal_entrenamiento.md).")
    if args.subir_hf:
        subir_a_hf(args.subir_hf, args.salida, resumen)


def subir_a_hf(repo: str, carpeta: Path, resumen: dict) -> None:
    """Sube train/val/resumen a un repo privado de dataset y etiqueta la revisión con el hash de train."""
    import os
    from huggingface_hub import HfApi
    api = HfApi(token=os.environ.get("HF_TOKEN"))
    api.create_repo(repo, repo_type="dataset", private=True, exist_ok=True)
    etiqueta = "train-" + resumen["archivos"]["train"]["sha256"][:12]
    info = api.upload_folder(repo_id=repo, repo_type="dataset", folder_path=str(carpeta),
                             allow_patterns=["train.jsonl", "val.jsonl", "resumen.json"],
                             commit_message=f"datos de entrenamiento {etiqueta}")
    api.create_tag(repo, tag=etiqueta, repo_type="dataset", revision=info.oid, exist_ok=True)
    print(f"Subido a https://huggingface.co/datasets/{repo} (revisión {info.oid}, etiqueta {etiqueta})")


if __name__ == "__main__":
    main()
