"""Molde común: todo agente recibe el expediente, hace su parte y lo devuelve."""
from __future__ import annotations

from ..expediente import Expediente


class Agente:
    nombre = "agente"

    def trabajar(self, exp: Expediente) -> Expediente:
        raise NotImplementedError(f"{self.nombre.upper()} todavía no está construido.")
