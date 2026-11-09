"""ARCHIVO — MEMORIA Y SEGUIMIENTO.

Momentos de trabajo:
- consultar(exp): ANTES de empezar
    · llena exp.historial_previo con guías anteriores del mismo curso y asignatura;
    · llena exp.lecciones con las correcciones APROBADAS por el profesor,
      para que ATENEA, BAUHAUS y REVISOR las apliquen en esta guía.
- guardar(exp): AL FINAL, guarda la guía aprobada (curso / asignatura / fecha)
  y propone como "corrección" cada problema que REVISOR encontró en el camino.
- registrar_intento(exp): si la guía no se aprobó, igual anota sus problemas.

Archivos que mantiene:
- registro.json (en el almacén)       → todas las guías aprobadas (seguimiento curricular)
- datos/memoria/correcciones.json     → propuestas, aprobadas y descartadas
- contenidos/LECCIONES_APROBADAS.md   → resumen que ATENEA lee antes de escribir
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import memoria
from ..almacenamiento.local import AlmacenLocal
from ..expediente import Expediente
from .base import Agente
from .bauhaus import slug


class Archivo(Agente):
    nombre = "archivo"

    def __init__(self, almacen=None):
        self.almacen = almacen or AlmacenLocal()

    def _leer_lista(self, nombre):
        return json.loads(self.almacen.leer_texto(nombre)) if nombre in self.almacen.listar() else []

    def _escribir_lista(self, nombre, lista):
        self.almacen.guardar_texto(nombre, json.dumps(lista, ensure_ascii=False, indent=2))

    def consultar(self, exp: Expediente) -> Expediente:
        e = exp.encargo
        exp.historial_previo = [g for g in self._leer_lista("registro.json")
                                if g["asignatura"] == e.asignatura and set(g["cursos"]) & set(e.cursos)]
        exp.lecciones = memoria.aprobadas(e.asignatura)
        memoria.escribir_lecciones()
        exp.cambiar_estado("con_historial")
        exp.anotar("archivo", "atenea", "entrega",
                   f"{len(exp.historial_previo)} guía(s) anteriores de {e.asignatura} para "
                   f"{', '.join(e.cursos)} y {len(exp.lecciones)} lección(es) aprobada(s).")
        return exp

    def _proponer_correcciones(self, exp: Expediente) -> int:
        guia = f"{exp.encargo.fecha} {exp.encargo.asignatura} {', '.join(exp.encargo.cursos)}"
        n = 0
        for m in exp.bitacora:
            if m.tipo == "solicitud_correccion":
                seccion = m.texto[1:m.texto.find("]")] if m.texto.startswith("[") else "general"
                if memoria.proponer(m.para, seccion, m.texto.split("] ", 1)[-1], guia):
                    n += 1
        return n

    def registrar_intento(self, exp: Expediente) -> None:
        n = self._proponer_correcciones(exp)
        exp.anotar("archivo", "profesor", "aviso", f"{n} corrección(es) nueva(s) propuesta(s) para revisar.")

    def guardar(self, exp: Expediente) -> Expediente:
        e = exp.encargo
        carpeta = f"{slug('_'.join(e.cursos))}/{slug(e.asignatura)}/{e.fecha}_{slug(e.tema or 'guia')}"
        guardados = {}
        for clave, ruta in exp.archivos.items():
            if clave != "carpeta" and Path(ruta).is_file():
                destino = f"{carpeta}/{Path(ruta).name}"
                self.almacen.guardar_archivo(destino, Path(ruta))
                guardados[clave] = destino

        registro = self._leer_lista("registro.json")
        oa = [f"{o['codigo']} ({o['estado']})" for o in exp.contenido.get("oa_verificacion", []) if o.get("codigo")]
        registro.append({"fecha": e.fecha, "asignatura": e.asignatura, "cursos": e.cursos,
                         "numero": e.numero, "tema": e.tema, "oa": oa, "carpeta": carpeta,
                         "archivos": guardados})
        self._escribir_lista("registro.json", registro)

        n = self._proponer_correcciones(exp)
        exp.cambiar_estado("archivado")
        exp.anotar("archivo", "profesor", "entrega",
                   f"Guía guardada en el archivo: {carpeta}. Correcciones nuevas propuestas: {n}.")
        self.almacen.guardar_texto(f"{carpeta}/expediente.json", exp.a_json())
        return exp
