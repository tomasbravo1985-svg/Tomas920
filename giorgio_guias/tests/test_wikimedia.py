"""Reglas de la herramienta de Wikimedia Commons (sin conexión a internet)."""
import importlib.util

from giorgio.configuracion import RAIZ

spec = importlib.util.spec_from_file_location("wikimedia", RAIZ / "herramientas" / "wikimedia.py")
wm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wm)


def test_solo_licencias_libres_que_permiten_adaptar():
    for ok in ("CC BY 4.0", "CC BY-SA 3.0", "CC0", "Public domain", "CC-BY-SA-4.0"):
        assert wm.licencia_aceptable(ok), ok
    for no in ("CC BY-NC 2.0", "CC BY-ND 4.0", "CC BY-NC-SA 2.0", "All rights reserved", ""):
        assert not wm.licencia_aceptable(no), no


def test_descarga_reducida_a_1920_px():
    orig = "https://upload.wikimedia.org/wikipedia/commons/8/84/Foto_X.jpg"
    assert wm.url_descarga(orig, 4000) == \
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Foto_X.jpg/1920px-Foto_X.jpg"
    assert wm.url_descarga(orig, 1200) == orig      # ya es pequeña: se usa la original
