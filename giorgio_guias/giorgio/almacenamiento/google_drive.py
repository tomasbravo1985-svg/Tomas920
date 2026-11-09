"""Almacén en Google Drive — PREPARADO, NO ACTIVO.

Se construirá solo cuando el profesor lo autorice. No se conecta a nada hoy.
"""
from __future__ import annotations

from .base import Almacen


class AlmacenGoogleDrive(Almacen):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "La conexión con Google Drive aún no está activada. "
            "Usa tipo = \"local\" en config/sistema.toml."
        )
