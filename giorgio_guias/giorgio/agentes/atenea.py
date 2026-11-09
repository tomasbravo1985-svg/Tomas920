"""ATENEA — PEDAGOGÍA.

Recibe: el encargo + el historial previo (de ARCHIVO) + observaciones (de REVISOR).
Entrega: exp.contenido, un diccionario con una entrada por cada sección
         de config/formato_guia.toml (objetivo, actividades, lectura, preguntas,
         palabras para sopa de letras y crucigrama, respuestas correctas, etc.).

Responsabilidades:
- Planificar contenidos y objetivos según el currículum chileno (Bases Curriculares, OA).
- Elaborar actividades y adaptar la dificultad al nivel.
- Evitar repetir temas que ARCHIVO informa como ya trabajados.
"""
from .base import Agente


class Atenea(Agente):
    nombre = "atenea"
