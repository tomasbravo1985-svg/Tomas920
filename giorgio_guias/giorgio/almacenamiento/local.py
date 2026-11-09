"""Almacén en una carpeta de tu computador (datos/archivo)."""
from __future__ import annotations

from pathlib import Path

from ..configuracion import RAIZ
from .base import Almacen


class AlmacenLocal(Almacen):
    def __init__(self, carpeta: str | Path | None = None):
        self.carpeta = Path(carpeta) if carpeta else RAIZ / "datos" / "archivo"

    def guardar_texto(self, ruta: str, texto: str) -> None:
        destino = self.carpeta / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")

    def leer_texto(self, ruta: str) -> str:
        return (self.carpeta / ruta).read_text(encoding="utf-8")

    def listar(self, carpeta: str = "") -> list[str]:
        base = self.carpeta / carpeta
        if not base.exists():
            return []
        return sorted(str(p.relative_to(self.carpeta)) for p in base.rglob("*") if p.is_file())
