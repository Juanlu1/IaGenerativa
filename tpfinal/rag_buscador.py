"""Buscador local de normas para el TP final.

Usa las normas que recibe en cada corrida. No guarda valores de parámetros ni
necesita un modelo, una base externa o acceso a la red durante la operación.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from admision.normas import cargar_normas


_PALABRA = re.compile(r"[a-z0-9]+")
_APARTADO = re.compile(r"(?=^§\d+\.)", re.MULTILINE)
_PARAMETRO = re.compile(r"P-[A-Z]{3}-\d+")
_PAR_VALOR = re.compile(r"(P-[A-Z]{3}-\d+) = ([^;.]+)")
_STOP = frozenset(
    "a al algo ante antes asi aun aunque cada como con cual cuales cuando de del desde "
    "donde durante el ella ellos en entre era es esta este esto estos hasta hay la las le "
    "lo los mas me mi mis no nos o para pero por porque que quien se si sin sobre su sus "
    "tambien te tengo tiene tienen todo un una uno unos y ya hacer hace debe puedo puede "
    "paciente admision hospital guardia norma seccion".split()
)

# Equivalencias de vocabulario clínico/administrativo; no contienen decisiones
# ni valores de las normas. Ayudan a recuperar reglas redactadas formalmente a
# partir de preguntas coloquiales.
_CONCEPTOS = {
    "documento": ("dni", "cedula", "pasaporte", "identidad", "papeles"),
    "registro": ("registrar", "anotar", "cargar", "ficha", "datos"),
    "box": ("ubicar", "pasar", "adentro", "consultorio", "sala"),
    "cobertura": ("obra social", "prepaga", "credencial", "afiliacion", "afiliado"),
    "art": ("trabajo", "trabajando", "laboral", "empleador", "operario", "obrero", "albanil", "fabrica", "andamio"),
    "ecg": ("electrocardiograma", "pecho", "toracico", "corazon"),
    "acv": ("neurologico", "cara torcida", "derrame", "ictus"),
    "sepsis": ("infeccion", "shock", "antibiotico", "hemocultivos"),
    "ambulancia": ("traslado", "emergencia movil"),
    "derivacion": ("derivar", "mandar", "destino", "establecimiento"),
    "internacion": ("internar", "cama", "habitacion"),
    "voluntariado": ("voluntarios", "acompanamiento"),
}


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def _tokens(texto: str) -> list[str]:
    return [t[:5] if len(t) >= 6 else t
            for t in _PALABRA.findall(_normalizar(texto)) if t not in _STOP]


def _consulta_expandida(consulta: str) -> list[str]:
    normal = _normalizar(consulta)
    tokens = _tokens(consulta)
    for concepto, alias in _CONCEPTOS.items():
        menciona = (bool(re.search(r"(?<!\w)art(?!\w)", normal)) if concepto == "art"
                    else concepto in normal)
        if menciona or any(a in normal for a in alias):
            tokens.extend(_tokens(concepto))
    return tokens


@dataclass(frozen=True)
class Fragmento:
    seccion: str
    texto: str


class BuscadorNormas:
    """BM25 local sobre normas, con parámetros de la carpeta recibida."""

    def __init__(self, ruta_normas: str | Path, granularidad: str = "seccion"):
        if granularidad not in {"apartado", "seccion", "hibrido2", "hibrido3"}:
            raise ValueError("granularidad desconocida")
        self.k_entorno = 3 if granularidad == "apartado" else 2
        self._parrafos_por_seccion = int(granularidad[-1]) if granularidad.startswith("hibrido") else 0
        if self._parrafos_por_seccion:
            self._secciones = BuscadorNormas(ruta_normas, "seccion")
            self._apartados = BuscadorNormas(ruta_normas, "apartado")
            return
        self.fragmentos: list[Fragmento] = []
        for seccion in cargar_normas(Path(ruta_normas)):
            if granularidad == "seccion":
                self.fragmentos.append(Fragmento(seccion.id, seccion.texto))
                continue
            encabezado, _, cuerpo = seccion.cuerpo.partition("\n")
            valores = dict(_PAR_VALOR.findall(seccion.valores))
            apartados = [p.strip() for p in _APARTADO.split(cuerpo) if p.strip()]
            for apartado in apartados or [cuerpo.strip()]:
                citados = list(dict.fromkeys(_PARAMETRO.findall(apartado)))
                linea = "; ".join(f"{p} = {valores[p]}" for p in citados if p in valores)
                texto = f"{encabezado}\n{apartado}"
                if linea:
                    texto += f"\nValores: {linea}."
                self.fragmentos.append(Fragmento(seccion.id, texto))

        self._frecuencias = [Counter(_tokens(f.texto)) for f in self.fragmentos]
        self._largos = [sum(c.values()) for c in self._frecuencias]
        self._largo_medio = sum(self._largos) / max(len(self._largos), 1)
        apariciones = Counter(t for c in self._frecuencias for t in c)
        n = len(self.fragmentos)
        self._idf = {t: math.log(1 + (n - df + 0.5) / (df + 0.5)) for t, df in apariciones.items()}

    def recuperar(self, consulta: str, k: int) -> list[Fragmento]:
        if k <= 0:
            return []
        if self._parrafos_por_seccion:
            secciones = self._secciones.recuperar(consulta, k)
            apartados = self._apartados.recuperar(consulta, len(self._apartados.fragmentos))
            respuesta = []
            for seccion in secciones:
                elegidos = [f.texto for f in apartados if f.seccion == seccion.seccion][:self._parrafos_por_seccion]
                respuesta.append(Fragmento(seccion.seccion, "\n\n".join(elegidos)))
            return respuesta
        terminos = Counter(_consulta_expandida(consulta))
        resultados = []
        for i, (frecuencias, largo) in enumerate(zip(self._frecuencias, self._largos)):
            normalizador = 1.2 * (0.25 + 0.75 * largo / max(self._largo_medio, 1))
            puntaje = sum(
                self._idf.get(t, 0) * (f * 2.2 / (f + normalizador)) * min(peso, 2)
                for t, peso in terminos.items()
                if (f := frecuencias.get(t, 0))
            )
            resultados.append((puntaje, i))
        resultados.sort(key=lambda x: (-x[0], x[1]))
        return [self.fragmentos[i] for _, i in resultados[:k]]


def construir_buscador(ruta_normas: str | Path) -> BuscadorNormas:
    return BuscadorNormas(ruta_normas)
