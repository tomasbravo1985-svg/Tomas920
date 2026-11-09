"""Lee los archivos de la carpeta config/ (formato TOML, fácil de editar a mano)."""
from __future__ import annotations

import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_CONFIG = RAIZ / "config"


def leer(nombre: str) -> dict:
    """Ejemplo: leer("escuela") abre config/escuela.toml."""
    with open(CARPETA_CONFIG / f"{nombre}.toml", "rb") as f:
        return tomllib.load(f)
