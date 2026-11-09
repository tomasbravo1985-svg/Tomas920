"""Comprueba que los archivos de configuración existen y dicen lo correcto."""
from giorgio import configuracion


def test_escuela():
    esc = configuracion.leer("escuela")
    assert esc["escuela"]["nombre"] == "Escuela Rebeca Matte Bello"
    assert esc["privacidad"]["guardar_datos_de_estudiantes"] is False


def test_formato_tiene_todas_las_secciones_en_orden():
    fmt = configuracion.leer("formato_guia")
    assert fmt["pagina"]["tamano"] == "carta"
    assert fmt["pagina"]["orientacion"] == "vertical"
    assert fmt["pagina"]["caras_minimas"] >= 4
    assert fmt["pagina"]["duracion_minutos"] == 90
    assert fmt["encabezado"]["campos"] == ["Nombre", "Curso", "Fecha"]
    ids = [s["id"] for s in fmt["secciones"]]
    assert ids == [
        "actividad_inicial", "sopa_de_letras", "crucigrama", "lectura",
        "analisis_imagenes", "seleccion_unica", "verdadero_falso",
        "aplicacion", "ticket_salida",
    ]


def test_produccion_semanal_son_cinco_guias():
    guias = configuracion.leer("produccion_semanal")["guias"]
    assert len(guias) == 5
    asignaturas = [g["asignatura"] for g in guias]
    assert asignaturas.count("Historia, Geografía y Ciencias Sociales") == 2
    assert asignaturas.count("Tecnología") == 1
    assert asignaturas.count("Proyecto de Regeneración") == 2


def test_reglas_de_seguridad_activas():
    seg = configuracion.leer("sistema")["seguridad"]
    assert not any(seg.values()), "Ninguna acción riesgosa debe estar activada"
