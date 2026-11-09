"""Sopa de letras y crucigrama: se prueban con muchas semillas distintas."""
import pytest

from giorgio import cuadriculas as cu

PALABRAS = ["Desierto", "Altiplano", "Costa", "Cordillera", "Valle", "Bosque",
            "Glaciar", "Patagonia", "Clima", "Relieve", "Lluvia", "Antártica"]
PISTAS = [{"palabra": p, "pista": f"pista de {p}"} for p in
          ["Atacama", "Llama", "Oasis", "Pesca", "Agricultura", "Araucaria", "Viento", "Hielo", "Volcán"]]


def test_normalizar_quita_tildes_y_conserva_enie():
    assert cu.normalizar("Antártica") == "ANTARTICA"
    assert cu.normalizar("Ñandú") == "ÑANDU"
    with pytest.raises(ValueError):
        cu.normalizar("año 2024")


@pytest.mark.parametrize("semilla", range(10))
def test_sopa_contiene_todas_las_palabras(semilla):
    sopa = cu.crear_sopa(PALABRAS, tamano=14, semilla=semilla)
    assert len(sopa["grilla"]) == 14 and all(len(f) == 14 for f in sopa["grilla"])
    for p in PALABRAS:
        assert cu.buscar_en_sopa(sopa["grilla"], p), p


def test_sopa_rechaza_palabra_que_no_cabe():
    with pytest.raises(ValueError):
        cu.crear_sopa(["Electrodomestico"], tamano=10)


@pytest.mark.parametrize("semilla", range(10))
def test_crucigrama_correcto(semilla):
    cruci = cu.crear_crucigrama(PISTAS, semilla=semilla)
    assert cu.verificar_crucigrama(cruci) == []
    assert len(cruci["palabras"]) == len(PISTAS)
    assert all(p["numero"] >= 1 for p in cruci["palabras"])


def test_revisor_detecta_crucigrama_danado():
    cruci = cu.crear_crucigrama(PISTAS)
    p = cruci["palabras"][0]
    cruci["grilla"][p["fila"]][p["col"]] = "Z" if p["palabra"][0] != "Z" else "Y"
    assert cu.verificar_crucigrama(cruci)
