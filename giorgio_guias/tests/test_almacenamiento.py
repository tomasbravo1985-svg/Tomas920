import pytest

from giorgio.agentes import Archivo, Atenea, Bauhaus, Revisor
from giorgio.almacenamiento.google_drive import AlmacenGoogleDrive
from giorgio.almacenamiento.local import AlmacenLocal


def test_almacen_local_guarda_y_lee(tmp_path):
    alm = AlmacenLocal(tmp_path)
    alm.guardar_texto("6C/historia/2026-11-09/guia.json", "{}")
    assert alm.leer_texto("6C/historia/2026-11-09/guia.json") == "{}"
    assert alm.listar() == ["6C/historia/2026-11-09/guia.json"]


def test_google_drive_esta_desactivado():
    with pytest.raises(NotImplementedError):
        AlmacenGoogleDrive()


def test_los_cuatro_agentes_existen():
    nombres = {Atenea.nombre, Bauhaus.nombre, Revisor.nombre, Archivo.nombre}
    assert nombres == {"atenea", "bauhaus", "revisor", "archivo"}
