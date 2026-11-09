"""Las pruebas trabajan en carpetas temporales: nunca tocan la memoria,
el catálogo de imágenes ni el logo reales del profesor."""
import pytest

from giorgio import curriculo, memoria, recursos


@pytest.fixture(autouse=True)
def carpetas_temporales(tmp_path, monkeypatch):
    rec = tmp_path / "recursos"
    monkeypatch.setattr(recursos, "CARPETA", rec)
    monkeypatch.setattr(recursos, "CATALOGO", rec / "catalogo.json")
    monkeypatch.setattr(recursos, "ENTRADA", rec / "entrada")
    monkeypatch.setattr(recursos, "IMAGENES", rec / "imagenes")
    monkeypatch.setattr(recursos, "LOGO", rec / "logo" / "logo_escuela.png")
    monkeypatch.setattr(recursos, "PEDIDO", rec / "entrada" / "PEDIDO_DE_IMAGENES.md")
    monkeypatch.setattr(memoria, "ARCHIVO_MEMORIA", tmp_path / "memoria" / "correcciones.json")
    monkeypatch.setattr(memoria, "LECCIONES_MD", tmp_path / "LECCIONES_APROBADAS.md")
    monkeypatch.setattr(curriculo, "REGISTRO", tmp_path / "oa_verificados.json")
    return tmp_path
