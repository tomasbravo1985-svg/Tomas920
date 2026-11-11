"""Regla GG-001 (extensión flexible), tiempos de 90 minutos, nivel de pensamiento y diagramación."""
import json

import pytest

from giorgio import maqueta, memoria, tiempos
from giorgio.agentes import Atenea, Revisor
from giorgio.configuracion import RAIZ, leer
from giorgio.expediente import Encargo, Expediente

V2 = RAIZ / "contenidos" / "2026-11_historia_6C_ambientes_naturales_v2.json"
GG = next(r for r in leer("reglas_aprobadas")["reglas"] if r["codigo"] == "GG-001")["valor"]


def test_gg001_queda_registrada_como_aprobada_con_fecha():
    memoria.sincronizar_reglas_oficiales()
    memoria.sincronizar_reglas_oficiales()          # no se duplica
    gg = [c for c in memoria.cargar() if c.get("codigo") == "GG-001"]
    assert len(gg) == 1
    assert gg[0]["estado"] == "aprobada" and gg[0]["fecha_aprobacion"] == "2026-11-10"
    assert "mínimo de cuatro páginas" in gg[0]["descripcion"]
    reglas = memoria.reglas(memoria.aprobadas())
    assert reglas["paginas_minimas"] == 4 and reglas["paginas_maximas"] == 0   # sin máximo rígido
    assert "GG-001" in memoria.LECCIONES_MD.read_text(encoding="utf-8")


def test_niveles_ya_no_tienen_maximo_de_paginas():
    assert all("paginas_maximas" not in g for g in leer("niveles").values())


def _expediente(cambios=None, tmp_path=None):
    datos = json.loads(V2.read_text(encoding="utf-8"))
    if cambios:
        cambios(datos)
    ruta = tmp_path / "c.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    exp = Expediente(encargo=Encargo(**datos["encargo"], fuente_contenido=str(ruta)))
    memoria.sincronizar_reglas_oficiales()
    exp.lecciones = memoria.aprobadas()
    return Atenea().trabajar(exp)


def _revisar(exp):
    from giorgio import cuadriculas
    exp.diseno = {"sopa": cuadriculas.crear_sopa(exp.contenido["sopa_de_letras"]["palabras"], 14, 3),
                  "crucigrama": cuadriculas.crear_crucigrama(exp.contenido["crucigrama"]["pistas"]),
                  "imagenes": [], "logo": ""}
    return Revisor().trabajar(exp).revision


def _problemas(r):
    return " ".join(o["problema"] for o in r["observaciones"])


# ------------------------------------------------------------------ tiempos
def test_estimacion_de_tiempo_del_ejemplo_es_coherente():
    c = json.loads(V2.read_text(encoding="utf-8"))
    total = sum(tiempos.estimar(c).values())
    assert 0.85 * 90 <= total <= 1.15 * 90
    assert sum(tiempos.minutos_propuestos(c).values()) == 90


def test_revisor_exige_secuencia_y_que_sume_90(tmp_path):
    r = _revisar(_expediente(lambda d: d["secuencia"].pop("lectura"), tmp_path))
    assert "Faltan los minutos" in _problemas(r)
    def mal(d):
        d["secuencia"]["lectura"]["minutos"] = 50
    assert "suman" in _problemas(_revisar(_expediente(mal, tmp_path)))


def test_revisor_detecta_guia_con_poco_trabajo_para_90_min(tmp_path):
    def poco(d):
        d["lectura"]["preguntas"] = d["lectura"]["preguntas"][:3]
        for sec in ("actividad_inicial", "lectura", "ticket_salida"):
            for q in d[sec]["preguntas"]:
                q["lineas"] = 1
        d["aplicacion"].update({"lineas": 1, "recuadro_dibujo": False, "pasos": ["Escribe."]})
        d["analisis_imagenes"]["preguntas"] = []
        d["analisis_imagenes"].pop("tabla")
    assert "no alcanza" in _problemas(_revisar(_expediente(poco, tmp_path)))


def test_revisor_detecta_exceso_de_relleno(tmp_path):
    def relleno(d):
        d["secuencia"]["sopa_de_letras"]["minutos"] = 20
        d["secuencia"]["crucigrama"]["minutos"] = 20
        d["secuencia"]["lectura"]["minutos"] = 5
        d["secuencia"]["analisis_imagenes"]["minutos"] = 7
    assert "repaso" in _problemas(_revisar(_expediente(relleno, tmp_path)))


# ------------------------------------------------------------------ pensamiento
def test_clasificacion_de_preguntas():
    assert tiempos.nivel("¿Qué ambiente está en el norte?") == "recordar"
    assert tiempos.nivel("¿Por qué Chile tiene paisajes distintos?") == "comprender"
    assert tiempos.nivel("Compara el desierto con el bosque.") == "analizar"
    assert tiempos.nivel("Imagina que viajas al sur y diseña una postal.") == "aplicar"


def test_revisor_rechaza_guia_de_solo_recordar(tmp_path):
    def memorista(d):
        for sec in ("actividad_inicial", "lectura", "ticket_salida", "analisis_imagenes"):
            for q in d[sec].get("preguntas", []):
                q["texto"] = "¿Qué dice el texto?"
        d["seleccion_unica"]["preguntas"] = d["seleccion_unica"]["preguntas"] * 2
    assert "solo recordar" in _problemas(_revisar(_expediente(memorista, tmp_path)))


# ------------------------------------------------------------------ diagramación (sin PDF real)
def _pagina(n, ocupacion=0.9, titulos=(), imagenes=(), **extra):
    base = {"numero": n, "ocupacion": ocupacion, "desbordes": 0, "letra_pequena": [], "titulos": list(titulos),
            "imagenes": list(imagenes), "filas_sopa": 0, "tiene_crucigrama": False, "tiene_horizontales": False,
            "tiene_verticales": False, "tiene_recuadro_dibujo": False, "tiene_aplicacion": False, "texto": ""}
    base.update(extra)
    return base


def test_maqueta_detecta_problemas_graves():
    img = {"ancho_cm": 7.4, "alto_cm": 5, "arriba": 300}
    analisis = {"total": 4, "paginas": [
        _pagina(1, titulos=[{"numero": 1, "texto": "ACTIVIDAD 1", "posicion": 0.1}], filas_sopa=5),
        _pagina(2, ocupacion=0.2, filas_sopa=8, imagenes=[img],
                titulos=[{"numero": 2, "texto": "ACTIVIDAD 2", "posicion": 0.95}]),
        _pagina(3, imagenes=[img], letra_pequena=[("texto chico", 7.0)], desbordes=2),
        _pagina(4, tiene_aplicacion=True), ]}
    analisis["paginas"][3]["titulos"] = [{"numero": 3, "texto": "ACTIVIDAD 3 │ APLICACIÓN", "posicion": 0.1}]
    analisis["paginas"][2]["tiene_recuadro_dibujo"] = True
    graves = " ".join(maqueta.problemas(analisis, GG)["graves"])
    for texto in ("casi vacía", "solo al final", "partida", "repartidas", "pequeña", "fuera de los márgenes",
                  "separadas de su recuadro"):
        assert texto in graves, texto


def test_maqueta_acepta_guia_larga_sin_maximo():
    analisis = {"total": 14, "paginas": [_pagina(i, titulos=[{"numero": i, "texto": f"ACTIVIDAD {i}", "posicion": 0.1}])
                                        for i in range(1, 15)]}
    assert maqueta.problemas(analisis, GG)["graves"] == []


def test_maqueta_exige_minimo_de_cuatro():
    analisis = {"total": 3, "paginas": [_pagina(i) for i in range(1, 4)]}
    assert any("mínimo aprobado" in g for g in maqueta.problemas(analisis, GG)["graves"])


def test_maqueta_reconoce_titulos_con_minutos_y_frases_que_anuncian():
    """Regresión: con '⏱ 9 min' en el título, el crucigrama separado de sus pistas no se detectaba."""
    analisis = {"total": 4, "paginas": [
        _pagina(1, titulos=[{"numero": 1, "texto": "ACTIVIDAD 1 │ CRUCIGRAMA ⏱ 9 min", "posicion": 0.7}],
                tiene_crucigrama=True, ultima_linea="Corrige aquí las afirmaciones falsas:"),
        _pagina(2, tiene_horizontales=True, tiene_verticales=True),
        _pagina(3, imagenes=[{"ancho_cm": 7.4, "alto_cm": 5, "arriba": 300}]),
        _pagina(4, tiene_tabla_imagenes=True)]}
    pr = maqueta.problemas(analisis, GG)
    graves = " ".join(pr["graves"])
    assert "separado de sus pistas" in graves
    assert "anuncia" in graves
    assert any("páginas distintas" in l for l in pr["leves"])
