"""ARCHIVO — MEMORIA Y SEGUIMIENTO.

Tiene dos momentos de trabajo:
- consultar(exp): ANTES de empezar, llena exp.historial_previo con guías
  anteriores del mismo curso y asignatura (para no repetir).
- guardar(exp): AL FINAL, guarda la guía aprobada ordenada por
  curso / asignatura / fecha, y registra las correcciones para reutilizarlas.

Archivos que mantiene dentro del almacén:
- registro.json      → lista de todas las guías aprobadas (seguimiento curricular)
- correcciones.json  → todo lo que REVISOR tuvo que corregir alguna vez
- <curso>/<asignatura>/<fecha>_<tema>/  → Word, PDF, solucionario y expediente

Usa un "almacén" intercambiable: hoy la carpeta local, mañana Google Drive.
"""
from __future__ import annotations

import json
from pathlib import Path

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
        exp.cambiar_estado("con_historial")
        exp.anotar("archivo", "atenea", "entrega",
                   f"{len(exp.historial_previo)} guía(s) anteriores de {e.asignatura} para {', '.join(e.cursos)}.")
        return exp

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
        registro.append({"fecha": e.fecha, "asignatura": e.asignatura, "cursos": e.cursos,
                         "numero": e.numero, "tema": e.tema, "carpeta": carpeta, "archivos": guardados})
        self._escribir_lista("registro.json", registro)

        correcciones = self._leer_lista("correcciones.json")
        for m in exp.bitacora:
            if m.tipo == "solicitud_correccion":
                correcciones.append({"fecha": e.fecha, "asignatura": e.asignatura, "para": m.para, "problema": m.texto})
        self._escribir_lista("correcciones.json", correcciones)

        exp.cambiar_estado("archivado")
        exp.anotar("archivo", "profesor", "entrega", f"Guía guardada en el archivo: {carpeta}")
        self.almacen.guardar_texto(f"{carpeta}/expediente.json", exp.a_json())
        return exp
