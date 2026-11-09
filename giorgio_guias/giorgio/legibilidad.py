"""Mide qué tan fácil de leer es un texto en español.

Usa el índice de Szigriszt-Pazos (escala INFLESZ), pensado para el español:
    menos de 40 = muy difícil · 40-55 = algo difícil · 55-65 = normal
    65-80 = bastante fácil · más de 80 = muy fácil
Es una ayuda, no un juicio final: el profesor siempre decide.
"""
from __future__ import annotations

import re
import unicodedata

FUERTES = set("aeoáéíóú")   # í y ú con tilde también rompen el diptongo
VOCALES = set("aeiouáéíóúü")


def _palabras(texto: str) -> list[str]:
    return re.findall(r"[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]+", texto)


def oraciones(texto: str) -> list[str]:
    partes = re.split(r"(?<=[.!?¡¿:;])\s+|\n+", texto.strip())
    return [p for p in partes if _palabras(p)]


def silabas(palabra: str) -> int:
    """Cuenta sílabas de forma aproximada (suficiente para medir legibilidad)."""
    p = palabra.lower()
    p = re.sub(r"qu([eiéí])", r"q\1", p)          # 'que', 'qui': la u no suena
    p = re.sub(r"gu([eiéí])", r"g\1", p)          # 'gue', 'gui'
    p = re.sub(r"y$", "i", p)                      # 'hoy', 'rey'
    n, anterior = 0, ""
    for letra in p:
        if letra in VOCALES:
            if anterior in VOCALES and (letra in FUERTES and anterior in FUERTES):
                n += 1                              # hiato: dos vocales fuertes
            elif anterior not in VOCALES:
                n += 1
        anterior = letra
    return max(1, n)


def indice_inflesz(texto: str) -> float:
    pal = _palabras(texto)
    ors = oraciones(texto)
    if not pal or not ors:
        return 100.0
    total_silabas = sum(silabas(p) for p in pal)
    return round(206.835 - 62.3 * total_silabas / len(pal) - len(pal) / len(ors), 1)


def escala(indice: float) -> str:
    if indice < 40:
        return "muy difícil"
    if indice < 55:
        return "algo difícil"
    if indice < 65:
        return "normal"
    if indice < 80:
        return "bastante fácil"
    return "muy fácil"


def contar_palabras(texto: str) -> int:
    return len(_palabras(texto))


def oraciones_largas(texto: str, maximo: int) -> list[str]:
    return [o for o in oraciones(texto) if len(_palabras(o)) > maximo]


def palabras_dificiles(texto: str, minimo_silabas: int = 5) -> list[str]:
    vistas = []
    for p in _palabras(texto):
        if silabas(p) >= minimo_silabas and p.lower() not in vistas:
            vistas.append(p.lower())
    return vistas


def sin_tildes(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")
