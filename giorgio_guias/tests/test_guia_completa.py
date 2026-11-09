"""Prueba de punta a punta: los 4 agentes reales crean la guía de ejemplo.
Necesita LibreOffice (para el PDF); si no está instalado, la prueba se salta."""
import json
from pathlib import Path

import pytest

from giorgio.agentes import Archivo, Atenea, Bauhaus, Revisor
from giorgio.agentes.bauhaus import buscar_libreoffice
from giorgio.almacenamiento.local import AlmacenLocal
from giorgio.configuracion import RAIZ
from giorgio.expediente import Encargo
from giorgio.orquestador import producir_guia

EJEMPLO = RAIZ / "contenidos" / "2026-11_historia_6C_ambientes_naturales.json"
pytestmark = pytest.mark.skipif(not buscar_libreoffice(), reason="LibreOffice no instalado")


def _encargo():
    datos = json.loads(EJEMPLO.read_text(encoding="utf-8"))
    return Encargo(**datos["encargo"], fuente_contenido=str(EJEMPLO))


def test_guia_de_ejemplo_se_aprueba_y_archiva(tmp_path):
    archivo = Archivo(AlmacenLocal(tmp_path / "archivo"))
    exp = producir_guia(_encargo(), archivo, Atenea(), Bauhaus(tmp_path / "salida"), Revisor())
    assert exp.estado == "archivado", exp.revision
    assert Path(exp.archivos["pdf"]).is_file()
    assert Path(exp.archivos["solucionario_pdf"]).is_file()
    archivados = archivo.almacen.listar()
    assert "registro.json" in archivados
    assert any(a.endswith(".pdf") for a in archivados)


def test_no_repite_un_tema_ya_archivado(tmp_path):
    archivo = Archivo(AlmacenLocal(tmp_path / "archivo"))
    producir_guia(_encargo(), archivo, Atenea(), Bauhaus(tmp_path / "s1"), Revisor())
    exp = producir_guia(_encargo(), archivo, Atenea(), Bauhaus(tmp_path / "s2"), Revisor())
    assert exp.estado == "requiere_profesor"
    assert any(o["seccion"] == "tema" for o in exp.revision["observaciones"])


def test_revisor_rechaza_contenido_incompleto(tmp_path):
    datos = json.loads(EJEMPLO.read_text(encoding="utf-8"))
    datos["seleccion_unica"]["preguntas"][0]["alternativas"] = ["solo", "tres", "alternativas"]
    del datos["verdadero_falso"]
    malo = tmp_path / "malo.json"
    malo.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    enc = Encargo(**datos["encargo"], fuente_contenido=str(malo))
    exp = producir_guia(enc, Archivo(AlmacenLocal(tmp_path / "a")), Atenea(),
                        Bauhaus(tmp_path / "s"), Revisor(), correcciones_maximas=0)
    assert exp.estado == "requiere_profesor"
    secciones = {o["seccion"] for o in exp.revision["observaciones"]}
    assert "verdadero_falso" in secciones


def test_word_respeta_el_orden_interno(tmp_path):
    """Microsoft Word muestra un error si los elementos internos están desordenados."""
    from docx import Document

    from giorgio.word import ORDEN
    exp = producir_guia(_encargo(), Archivo(AlmacenLocal(tmp_path / "a")), Atenea(),
                        Bauhaus(tmp_path / "s"), Revisor())
    for clave in ("docx", "solucionario_docx"):
        cuerpo = Document(exp.archivos[clave]).element
        ns = cuerpo.tag.split("}")[0] + "}"
        for padre, orden in ORDEN.items():
            for el in cuerpo.iter(padre.replace("w:", ns)):
                hijos = [h.tag.replace(ns, "w:") for h in el]
                posiciones = [orden.index(h) for h in hijos if h in orden]
                assert posiciones == sorted(posiciones), (padre, hijos)
                assert len(hijos) == len(set(hijos)), (padre, hijos)
