"""ATENEA — PEDAGOGÍA.

Recibe: el encargo + el historial previo (de ARCHIVO) + observaciones (de REVISOR).
Entrega: exp.contenido, un diccionario con una entrada por cada sección
         de config/formato_guia.toml (objetivo, actividades, lectura, preguntas,
         palabras para sopa de letras y crucigrama, respuestas correctas, etc.).

MODO MANUAL (el elegido por el profesor):
  Claude Code redacta el contenido en un archivo de la carpeta contenidos/
  y ATENEA lo carga, lo ordena y avisa si el tema ya se trabajó antes.
  Si REVISOR pide corregir contenido, ATENEA vuelve a leer el archivo
  (por si fue corregido) y deja el aviso para que Claude Code lo arregle.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..configuracion import RAIZ
from ..expediente import Expediente
from .base import Agente


class Atenea(Agente):
    nombre = "atenea"

    def trabajar(self, exp: Expediente) -> Expediente:
        ruta = Path(exp.encargo.fuente_contenido)
        if not ruta.is_absolute():
            ruta = RAIZ / ruta
        if not ruta.is_file():
            raise FileNotFoundError(f"ATENEA no encuentra el contenido: {ruta}")

        es_correccion = any(o["responsable"] == "atenea"
                            for o in exp.revision.get("observaciones", []))
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        datos.pop("encargo", None)
        exp.contenido = datos

        temas_previos = {h.get("tema", "").lower() for h in exp.historial_previo}
        if exp.encargo.tema.lower() in temas_previos:
            exp.anotar("atenea", "profesor", "aviso",
                       f"El tema '{exp.encargo.tema}' ya se trabajó con este curso.")

        if es_correccion:
            exp.anotar("atenea", "profesor", "aviso",
                       f"Modo manual: las correcciones de contenido se hacen en {ruta.name}.")
        exp.cambiar_estado("planificado")
        exp.anotar("atenea", "bauhaus", "entrega", f"Contenido listo: {datos.get('titulo', '')}")
        return exp
