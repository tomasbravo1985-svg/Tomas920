"""ARCHIVO — MEMORIA Y SEGUIMIENTO.

Tiene dos momentos de trabajo:
- consultar(exp): ANTES de empezar, llena exp.historial_previo con guías
  anteriores del mismo curso y asignatura (para no repetir).
- guardar(exp): AL FINAL, guarda la guía aprobada ordenada por
  curso / asignatura / fecha, y registra las correcciones para reutilizarlas.

Usa un "almacén" intercambiable: hoy la carpeta local, mañana Google Drive.
"""
from __future__ import annotations

from ..almacenamiento.local import AlmacenLocal
from ..expediente import Expediente
from .base import Agente


class Archivo(Agente):
    nombre = "archivo"

    def __init__(self, almacen=None):
        self.almacen = almacen or AlmacenLocal()

    def consultar(self, exp: Expediente) -> Expediente:
        raise NotImplementedError("ARCHIVO.consultar todavía no está construido.")

    def guardar(self, exp: Expediente) -> Expediente:
        raise NotImplementedError("ARCHIVO.guardar todavía no está construido.")
