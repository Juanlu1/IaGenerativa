"""Recuperador vectorial sobre el corpus del hospital (parte 1).

Uso desde las partes 2 y 3:

    from recuperador import Recuperador
    r = Recuperador.desde_config()
    r.buscar("¿Horario de visita en terapia intensiva?")   # -> list[str]

El contrato completo está en SPEC.md.
"""
import json
import re
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent
CONFIG = RAIZ / "config_rag.json"
CORPUS = RAIZ / "datos" / "corpus"


# ---------------- corpus y chunking ----------------

def leer_corpus(carpeta=CORPUS):
    """[(nombre de archivo, texto)] de los .md de la carpeta, en orden alfabético."""
    return [(p.name, p.read_text(encoding="utf-8")) for p in sorted(Path(carpeta).glob("*.md"))]


def _titulo_y_cuerpo(texto):
    lineas = texto.strip().splitlines()
    if lineas and lineas[0].startswith("# "):
        return lineas[0][2:].strip(), "\n".join(lineas[1:])
    return "", "\n".join(lineas)


def fragmentar_secciones(texto, metadatos):
    """Un fragmento por sección `##`; un documento sin secciones es un solo fragmento.

    El texto de introducción entre el título y la primera sección, si existe,
    es un fragmento aparte.
    """
    titulo, cuerpo = _titulo_y_cuerpo(texto)
    partes = re.split(r"^## +(.+)$", cuerpo, flags=re.M)
    # partes = [intro, sección1, cuerpo1, sección2, cuerpo2, ...]
    secciones = [(None, partes[0])] + list(zip(partes[1::2], partes[2::2]))
    frags = []
    for nombre, texto_seccion in secciones:
        texto_seccion = texto_seccion.strip()
        if not texto_seccion:
            continue
        if metadatos:
            encabezado = f"{titulo} — {nombre}" if nombre else titulo
            texto_seccion = f"{encabezado}\n{texto_seccion}"
        frags.append(texto_seccion)
    return frags


def fragmentar_ventana(texto, tam, solapamiento, metadatos):
    """Ventanas de `tam` palabras que se solapan en `solapamiento` palabras.

    Los títulos Markdown (líneas que empiezan con #) no entran en las ventanas;
    con metadatos, el título del documento se antepone a cada una.
    """
    if not 0 <= solapamiento < tam:
        raise ValueError("el solapamiento tiene que ser menor que el tamaño de la ventana")
    titulo, cuerpo = _titulo_y_cuerpo(texto)
    palabras = " ".join(l for l in cuerpo.splitlines() if not l.startswith("#")).split()
    paso = tam - solapamiento
    frags = []
    for inicio in range(0, len(palabras), paso):
        frags.append(" ".join(palabras[inicio:inicio + tam]))
        if inicio + tam >= len(palabras):
            break
    return [f"{titulo}\n{f}" for f in frags] if metadatos else frags


def fragmentar(texto, cfg):
    if cfg["chunking"] == "seccion":
        return fragmentar_secciones(texto, cfg["metadatos"])
    if cfg["chunking"] == "ventana":
        return fragmentar_ventana(texto, cfg["tam_ventana"], cfg["solapamiento"], cfg["metadatos"])
    raise ValueError(f"chunking desconocido: {cfg['chunking']}")


# ---------------- selección ----------------

def seleccionar(sims, k, umbral, margen):
    """Índices de los fragmentos a devolver, de más a menos similar (ver SPEC.md)."""
    orden = [int(i) for i in np.argsort(-sims, kind="stable")[:k]]
    mejor = sims[orden[0]]
    elegidos = [i for i in orden
                if (umbral is None or sims[i] >= umbral)
                and (margen is None or sims[i] >= mejor - margen)]
    return elegidos or orden[:1]


# ---------------- encoders ----------------

class EncoderBertPromedio:
    """BERT sin ajustar para similitud: promedio de la última capa, pesado por la máscara."""

    def __init__(self, modelo):
        import torch
        from transformers import AutoModel, AutoTokenizer
        self._torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(modelo)
        self.modelo = AutoModel.from_pretrained(modelo).eval()

    def _codificar(self, textos):
        torch = self._torch
        salidas = []
        with torch.no_grad():
            for i in range(0, len(textos), 16):
                lote = self.tokenizer(textos[i:i + 16], padding=True, truncation=True,
                                      max_length=512, return_tensors="pt")
                ultima = self.modelo(**lote).last_hidden_state
                mascara = lote["attention_mask"].unsqueeze(-1).float()
                salidas.append((ultima * mascara).sum(1) / mascara.sum(1))
        v = torch.cat(salidas).numpy()
        return v / np.linalg.norm(v, axis=1, keepdims=True)

    codificar_consultas = _codificar
    codificar_pasajes = _codificar


class EncoderOraciones:
    """Modelo entrenado para embeddings de oraciones (sentence-transformers)."""

    def __init__(self, modelo, prefijo_consulta="", prefijo_pasaje=""):
        from sentence_transformers import SentenceTransformer
        self.modelo = SentenceTransformer(modelo, device="cpu")
        self.prefijo_consulta, self.prefijo_pasaje = prefijo_consulta, prefijo_pasaje

    def _codificar(self, textos, prefijo):
        return self.modelo.encode([prefijo + t for t in textos], normalize_embeddings=True,
                                  convert_to_numpy=True, show_progress_bar=False)

    def codificar_consultas(self, textos):
        return self._codificar(textos, self.prefijo_consulta)

    def codificar_pasajes(self, textos):
        return self._codificar(textos, self.prefijo_pasaje)


ENCODERS = {
    "bert-base": lambda: EncoderBertPromedio("google-bert/bert-base-multilingual-cased"),
    "minilm": lambda: EncoderOraciones("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
    "e5-small": lambda: EncoderOraciones("intfloat/multilingual-e5-small", "query: ", "passage: "),
    "e5-base": lambda: EncoderOraciones("intfloat/multilingual-e5-base", "query: ", "passage: "),
    "bge-m3": lambda: EncoderOraciones("BAAI/bge-m3"),
}


def crear_encoder(nombre):
    if nombre not in ENCODERS:
        raise ValueError(f"encoder desconocido: {nombre} (opciones: {', '.join(ENCODERS)})")
    return ENCODERS[nombre]()


# ---------------- recuperador ----------------

class Recuperador:
    def __init__(self, cfg, encoder=None, corpus=None):
        self.cfg = cfg
        self.encoder = encoder or crear_encoder(cfg["encoder"])
        corpus = leer_corpus() if corpus is None else corpus
        self.fragmentos = [f for _, texto in corpus for f in fragmentar(texto, cfg)]
        self.embeddings = self.encoder.codificar_pasajes(self.fragmentos)

    @classmethod
    def desde_config(cls, ruta=None, encoder=None):
        """Recuperador con la configuración entregada (config_rag.json)."""
        cfg = json.loads(Path(ruta or CONFIG).read_text(encoding="utf-8"))
        return cls(cfg, encoder=encoder)

    def buscar(self, consulta, k=None):
        """Fragmentos relevantes para la consulta, de más a menos relevante. Nunca vacío."""
        q = self.encoder.codificar_consultas([consulta])[0]
        sims = self.embeddings @ q
        idx = seleccionar(sims, k or self.cfg["k"], self.cfg.get("umbral"), self.cfg.get("margen"))
        return [self.fragmentos[i] for i in idx]
