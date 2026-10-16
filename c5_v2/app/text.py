"""Utilidades de texto: normalización y similitud entre nombres de rol."""
import unicodedata
from typing import Set

PALABRAS_VACIAS = {"de", "del", "la", "el", "y", "en"}


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y con espacios simples."""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(sin_tildes.lower().split())


def palabras(texto: str) -> Set[str]:
    """Conjunto de palabras significativas de un texto normalizado."""
    return {p for p in normalizar(texto).split() if p not in PALABRAS_VACIAS}


def jaccard(a: str, b: str) -> float:
    """Similitud de Jaccard entre las palabras de dos textos (0 a 1)."""
    pa, pb = palabras(a), palabras(b)
    if not pa or not pb:
        return 0.0
    return len(pa & pb) / len(pa | pb)
