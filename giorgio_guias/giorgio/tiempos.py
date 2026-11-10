"""ESTIMADOR DE TIEMPOS Y NIVEL DE PENSAMIENTO.

1. Estima cuántos minutos necesita realmente un estudiante para cada actividad,
   según la cantidad de trabajo (palabras que leer, preguntas, líneas que escribir...).
   Así REVISOR compara: ¿los tiempos que propone ATENEA son realistas?
   ¿La guía alcanza (y no sobra) para 90 minutos?

2. Clasifica cada pregunta según lo que exige pensar:
   recordar → comprender → analizar → aplicar/crear.
   Una buena guía no se queda solo en "recordar".

Son estimaciones de referencia, no mediciones exactas: el profesor ajusta.
"""
from __future__ import annotations

import re

from .legibilidad import contar_palabras, sin_tildes

NIVELES = ("recordar", "comprender", "analizar", "aplicar")

_PATRONES = {
    "aplicar": r"\b(imagina|disena|crea|inventa|propon|propone|planifica|dibuja|escribe una? (postal|carta|mensaje)|"
               r"que harias|como podrias|podrian?|podemos|construye|elabora|resuelve|organiza)\b",
    "analizar": r"\b(compara|comparar|diferencia|diferencias|se parece|se parecen|relaciona|clasifica|justifica|"
                r"por que crees|que pasaria|ventaja|desventaja|causa|consecuencia|en comun|"
                r"explica por que|evalua|argumenta|cual es mejor|que ambiente presenta|mas dificil)\b",
    "comprender": r"\b(explica|por que|describe|como|que significa|resume|con tus palabras|ejemplo|"
                  r"crees|interpreta|aprendi|caracteristica)\b",
}


def nivel(texto: str) -> str:
    t = sin_tildes(texto)
    for clave in ("aplicar", "analizar", "comprender"):
        if re.search(_PATRONES[clave], t):
            return clave
    return "recordar"


def preguntas_con_nivel(c: dict) -> list[tuple[str, str, str]]:
    """(sección, texto, nivel) de cada consigna que el estudiante debe responder."""
    items = []
    for sec in ("actividad_inicial", "lectura", "analisis_imagenes", "ticket_salida"):
        for q in c.get(sec, {}).get("preguntas", []):
            items.append((sec, q["texto"], nivel(q["texto"])))
    for q in c.get("seleccion_unica", {}).get("preguntas", []):
        items.append(("seleccion_unica", q["texto"], nivel(q["texto"])))
    if c.get("analisis_imagenes", {}).get("tabla"):
        items.append(("analisis_imagenes", "Tabla: ambiente, característica, oportunidad, dificultad", "analizar"))
    if c.get("aplicacion"):
        items.append(("aplicacion", c["aplicacion"].get("titulo", "Aplicación"), "aplicar"))
    return items


def distribucion(c: dict) -> dict:
    items = preguntas_con_nivel(c)
    total = len(items) or 1
    return {n: round(sum(1 for _, _, x in items if x == n) / total, 2) for n in NIVELES} | {"total": len(items)}


# ------------------------------------------------------------------ tiempos
def _abierta(q: dict) -> float:
    """Pregunta abierta: leerla, pensar y escribir (≈0,7 min por línea)."""
    return 1.0 + 0.7 * q.get("lineas", 3)


def estimar(c: dict, palabras_por_minuto: int = 100) -> dict[str, float]:
    e = {}
    ai = c.get("actividad_inicial", {})
    e["actividad_inicial"] = 1.5 + sum(_abierta(q) for q in ai.get("preguntas", []))
    e["sopa_de_letras"] = 1.0 + 0.6 * len(c.get("sopa_de_letras", {}).get("palabras", []))
    e["crucigrama"] = 1.0 + 0.9 * len(c.get("crucigrama", {}).get("pistas", []))
    lec = c.get("lectura", {})
    e["lectura"] = (contar_palabras(" ".join(lec.get("parrafos", []))) / palabras_por_minuto
                    + sum(_abierta(q) for q in lec.get("preguntas", [])))
    im = c.get("analisis_imagenes", {})
    tabla = im.get("tabla") or {}
    celdas = len(tabla.get("filas", [])) * max(0, len(tabla.get("columnas", [])) - 1)
    e["analisis_imagenes"] = (1.0 * len(im.get("imagenes", [])) + 0.6 * celdas
                              + sum(_abierta(q) for q in im.get("preguntas", [])))
    e["seleccion_unica"] = 1.0 * len(c.get("seleccion_unica", {}).get("preguntas", []))
    vf = c.get("verdadero_falso", {}).get("afirmaciones", [])
    e["verdadero_falso"] = 0.7 * len(vf) + 1.0 * sum(1 for a in vf if a.get("respuesta") is False)
    ap = c.get("aplicacion", {})
    e["aplicacion"] = (3.0 + 1.0 * len(ap.get("pasos", [])) + 0.7 * ap.get("lineas", 0)
                       + (6.0 if ap.get("recuadro_dibujo") else 0))
    ts = c.get("ticket_salida", {})
    e["ticket_salida"] = 1.0 + sum(0.5 + 0.5 * q.get("lineas", 2) for q in ts.get("preguntas", []))
    return {k: round(v, 1) for k, v in e.items()}


def minutos_propuestos(c: dict) -> dict[str, int]:
    """Los tiempos que ATENEA asignó en su secuencia pedagógica."""
    return {k: v.get("minutos", 0) for k, v in c.get("secuencia", {}).items()}
