"""REVISOR — CALIDAD.

Recibe: exp.contenido + exp.archivos.
Entrega: exp.revision = {
    "aprobada": True/False,
    "observaciones": [
        {"responsable": "atenea" | "bauhaus", "seccion": "...", "problema": "..."},
    ],
}

Responsabilidades:
- Revisar coherencia pedagógica y que no falte ninguna sección.
- Comprobar que cada palabra está realmente en la sopa de letras / crucigrama.
- Detectar problemas de formato (páginas, márgenes, imágenes).
- Pedir correcciones al agente responsable antes de entregar.
"""
from .base import Agente


class Revisor(Agente):
    nombre = "revisor"
