"""ATENEA — PEDAGOGÍA.

Recibe: el encargo + el historial previo y las lecciones aprobadas (de ARCHIVO)
        + observaciones (de REVISOR).
Entrega: exp.contenido, con una entrada por cada sección de config/formato_guia.toml,
         y exp.contenido["oa_verificacion"]: el estado de cada Objetivo de Aprendizaje.

Objetivos de Aprendizaje (OA):
  ATENEA NO inventa números de OA. Compara el OA propuesto con el registro de OA
  verificados con fuente oficial (config/curriculo/oa_verificados.json).
  Si no puede verificarlo, queda "PENDIENTE DE CONFIRMACIÓN" y no se imprime
  en la guía del estudiante.

MODO MANUAL (el elegido por el profesor):
  Claude Code redacta el contenido en contenidos/ (después de leer
  contenidos/LECCIONES_APROBADAS.md) y ATENEA lo carga y lo verifica.
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import curriculo
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
        datos["oa_verificacion"] = curriculo.verificar(datos.get("oa"), exp.encargo.asignatura,
                                                       exp.encargo.cursos)
        exp.contenido = datos

        for oa in datos["oa_verificacion"]:
            if oa["estado"] == "pendiente":
                exp.anotar("atenea", "profesor", "aviso",
                           f"OA {oa['codigo'] or '(sin número)'} PENDIENTE DE CONFIRMACIÓN: {oa['motivo']}")

        temas_previos = {h.get("tema", "").lower() for h in exp.historial_previo}
        if exp.encargo.tema.lower() in temas_previos:
            exp.anotar("atenea", "profesor", "aviso",
                       f"El tema '{exp.encargo.tema}' ya se trabajó con este curso.")
        if exp.lecciones:
            exp.anotar("atenea", "bauhaus", "aviso",
                       f"Se consideraron {len(exp.lecciones)} lección(es) aprobada(s).")
        if es_correccion:
            exp.anotar("atenea", "profesor", "aviso",
                       f"Modo manual: las correcciones de contenido se hacen en {ruta.name}.")
        exp.cambiar_estado("planificado")
        exp.anotar("atenea", "bauhaus", "entrega", f"Contenido listo: {datos.get('titulo', '')}")
        return exp
