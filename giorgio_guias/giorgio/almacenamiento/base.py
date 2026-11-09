"""Contrato que debe cumplir cualquier lugar de almacenamiento.

Gracias a este molde, cambiar de carpeta local a Google Drive será
cambiar UNA línea en config/sistema.toml, sin tocar a los agentes.
"""
from __future__ import annotations


class Almacen:
    def guardar_texto(self, ruta: str, texto: str) -> None:
        raise NotImplementedError

    def guardar_archivo(self, ruta: str, origen) -> None:
        """Copia un archivo (Word, PDF) al almacén."""
        raise NotImplementedError

    def leer_texto(self, ruta: str) -> str:
        raise NotImplementedError

    def listar(self, carpeta: str = "") -> list[str]:
        raise NotImplementedError
