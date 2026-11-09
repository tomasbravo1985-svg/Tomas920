"""Pruebas de las mejoras: recursos visuales, logo, OA, legibilidad, memoria y REVISOR."""
import json

import pytest
from PIL import Image, ImageDraw

from giorgio import curriculo, legibilidad as leg, memoria, recursos
from giorgio.agentes import Archivo, Atenea, Bauhaus, Revisor
from giorgio.agentes.bauhaus import buscar_libreoffice
from giorgio.almacenamiento.local import AlmacenLocal
from giorgio.configuracion import RAIZ
from giorgio.expediente import Encargo
from giorgio.orquestador import producir_guia

EJEMPLO = RAIZ / "contenidos" / "2026-11_historia_6C_ambientes_naturales.json"
HISTORIA = "Historia, Geografía y Ciencias Sociales"
con_libreoffice = pytest.mark.skipif(not buscar_libreoffice(), reason="LibreOffice no instalado")


def foto(ruta, ancho=1400, alto=900, plana=False):
    im = Image.new("RGB", (ancho, alto), (128, 128, 128) if plana else "white")
    if not plana:
        d = ImageDraw.Draw(im)
        for i in range(0, ancho, 80):
            d.rectangle([i, 0, i + 40, alto], fill="black")
    im.save(ruta)
    return ruta


def contenido(tmp_path, cambios=None, nombre="c.json"):
    datos = json.loads(EJEMPLO.read_text(encoding="utf-8"))
    if cambios:
        cambios(datos)
    ruta = tmp_path / nombre
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return Encargo(**datos["encargo"], fuente_contenido=str(ruta))


# ------------------------------------------------------------------ recursos
def test_registrar_copia_sin_tocar_original_ni_sobrescribir(tmp_path):
    original = foto(tmp_path / "mi_foto.jpg")
    antes = original.read_bytes()
    f1 = recursos.registrar(original, "desierto_atacama", "fotografia", "Desierto", "Foto propia", "CC BY")
    f2 = recursos.registrar(original, "desierto_atacama", "fotografia")
    assert original.read_bytes() == antes and original.exists()
    assert f1["archivo"] != f2["archivo"]             # la segunda no sobrescribió la primera
    assert recursos.ficha("desierto_atacama")["estado"] == "disponible"


def test_pedido_e_importacion_desde_la_bandeja(tmp_path):
    recursos.pedir("mapa_chile", "mapa", "Mapa de Chile con sus regiones", "IDE Chile", "Historia 6.º C")
    assert "mapa_chile" in recursos.PEDIDO.read_text(encoding="utf-8")
    foto(recursos.ENTRADA / "mapa_chile.png")
    assert recursos.importar_entrada() == ["mapa_chile"]
    assert recursos.ruta_de("mapa_chile") is not None
    assert (recursos.ENTRADA / "mapa_chile.png").exists()   # el original sigue ahí
    assert "No falta ninguna imagen" in recursos.PEDIDO.read_text(encoding="utf-8")


def test_calidad_detecta_imagen_pequena_y_sin_contraste(tmp_path):
    mala = recursos.evaluar_calidad(foto(tmp_path / "x.png", 300, 200, plana=True), 7.0)
    assert len(mala["problemas"]) == 2
    buena = recursos.evaluar_calidad(foto(tmp_path / "y.png"), 7.0)
    assert buena["problemas"] == []


def test_logo_se_guarda_una_vez_y_conserva_el_anterior(tmp_path):
    recursos.registrar_logo(foto(tmp_path / "logo1.png", 600, 600))
    recursos.registrar_logo(foto(tmp_path / "logo2.png", 600, 600))
    assert recursos.logo_disponible()
    assert len(list(recursos.LOGO.parent.glob("logo_anterior_*.png"))) == 1


# ------------------------------------------------------------------ OA
def test_oa_sin_registro_queda_pendiente():
    r = curriculo.verificar("OA 12: Comparar ambientes", HISTORIA, ["6.º C"])
    assert r[0]["estado"] == "pendiente" and r[0]["codigo"] == "OA 12"


def test_oa_verificado_solo_si_coincide_con_la_fuente():
    curriculo.agregar(HISTORIA, "6", "OA 12", "Comparar diversos ambientes naturales en Chile.", "Fuente oficial X")
    assert curriculo.verificar({"codigo": "OA 12", "texto": "Comparar diversos ambientes naturales en Chile."},
                               HISTORIA, ["6.º C"])[0]["estado"] == "verificado"
    assert curriculo.verificar({"codigo": "OA 12", "texto": "Algo totalmente distinto"},
                               HISTORIA, ["6.º C"])[0]["estado"] == "pendiente"
    assert curriculo.verificar("OA 12", HISTORIA, ["7.º"])[0]["estado"] == "pendiente"   # otro nivel


def test_oa_exige_fuente_y_proyecto_es_institucional():
    with pytest.raises(ValueError):
        curriculo.agregar(HISTORIA, "6", "OA 1", "texto", "")
    assert curriculo.verificar(None, "Proyecto de Regeneración", ["7.º", "8.º"])[0]["estado"] == "institucional"


# ------------------------------------------------------------------ legibilidad
def test_silabas_y_legibilidad():
    assert [leg.silabas(p) for p in ("desierto", "país", "geografía", "que", "Antártica")] == [3, 2, 5, 1, 4]
    facil = "El sol sale. La casa es azul. Mi gato come pan."
    dificil = ("La conceptualización historiográfica contemporánea problematiza sistemáticamente "
               "las interpretaciones institucionalizadas, considerando simultáneamente multiplicidades.")
    assert leg.indice_inflesz(facil) > 80 > 40 > leg.indice_inflesz(dificil)


# ------------------------------------------------------------------ memoria
def test_memoria_propone_sin_duplicar_y_aprueba_con_regla():
    memoria.proponer("atenea", "lectura", "Lectura muy larga", "guía 1")
    assert memoria.proponer("atenea", "lectura", "Lectura muy larga", "guía 2") is None
    c = memoria.cargar()[0]
    assert c["veces"] == 2 and c["estado"] == "propuesta"
    memoria.aprobar(c["id"], {"tipo": "max_palabras_oracion", "valor": 18})
    assert memoria.reglas(memoria.aprobadas()) == {"max_palabras_oracion": 18}
    assert "Lectura muy larga" in memoria.LECCIONES_MD.read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        memoria.aprobar(c["id"], {"tipo": "inventada"})


# ------------------------------------------------------------------ REVISOR (sin PDF)
def _revisar(tmp_path, cambios, lecciones=None):
    exp = producir_guia.__globals__["Expediente"](encargo=contenido(tmp_path, cambios))
    exp.lecciones = lecciones or []
    exp = Atenea().trabajar(exp)
    from giorgio import cuadriculas
    exp.diseno = {"sopa": cuadriculas.crear_sopa(exp.contenido["sopa_de_letras"]["palabras"], 14, 3),
                  "crucigrama": cuadriculas.crear_crucigrama(exp.contenido["crucigrama"]["pistas"]),
                  "imagenes": [], "logo": ""}
    return Revisor().trabajar(exp).revision


def test_revisor_detecta_actividades_poco_claras(tmp_path):
    def danar(d):
        d["sopa_de_letras"]["instruccion"] = ""
        d["seleccion_unica"]["preguntas"][0]["alternativas"] = ["Polar", "Polar", "Frío", "Seco"]
        d["crucigrama"]["pistas"][0]["pista"] = "Desierto de Atacama, muy seco."
        d["lectura"]["parrafos"] = ["La conceptualización historiográfica contemporánea problematiza "
                                    "sistemáticamente interpretaciones institucionalizadas. "] * 3
    r = _revisar(tmp_path, danar)
    problemas = " ".join(o["problema"] for o in r["observaciones"])
    assert "Falta la instrucción" in problemas
    assert "alternativas repetidas" in problemas
    assert "contiene la respuesta" in problemas
    assert "muy difícil" in problemas


def test_revisor_aplica_palabras_prohibidas_aprobadas(tmp_path):
    leccion = {"estado": "aprobada", "regla": {"tipo": "palabras_prohibidas", "valor": ["creatividad"]}}
    r = _revisar(tmp_path, None, [leccion])
    assert any("creatividad" in o["problema"] for o in r["observaciones"])


def test_revisor_avisa_oa_pendiente(tmp_path):
    r = _revisar(tmp_path, None)
    assert any("PENDIENTE DE CONFIRMACIÓN" in a for a in r["advertencias"])


# ------------------------------------------------------------------ de punta a punta
@con_libreoffice
def test_falta_imagen_detiene_y_pide_la_foto(tmp_path):
    def foto_nueva(d):
        d["analisis_imagenes"]["imagenes"][0] = {"recurso": "salar_atacama", "pie": "Imagen A",
                                                 "tipo": "fotografia", "descripcion": "Salar de Atacama"}
    archivo = Archivo(AlmacenLocal(tmp_path / "a"))
    exp = producir_guia(contenido(tmp_path, foto_nueva), archivo, Atenea(), Bauhaus(tmp_path / "s"), Revisor())
    assert exp.estado == "requiere_profesor"
    assert exp.intentos_correccion == 0                       # no insiste: solo el profesor puede resolverlo
    assert "salar_atacama" in recursos.PEDIDO.read_text(encoding="utf-8")
    assert any(c["agente"] == "profesor" for c in memoria.cargar())   # ARCHIVO lo registró


@con_libreoffice
def test_logo_e_imagenes_reales_llegan_al_pdf(tmp_path):
    from pypdf import PdfReader
    recursos.registrar_logo(foto(tmp_path / "logo.png", 500, 500))
    recursos.registrar(foto(tmp_path / "f.jpg"), "paisaje_desierto", "fotografia", "Desierto", "Foto propia", "CC BY")
    exp = producir_guia(contenido(tmp_path), Archivo(AlmacenLocal(tmp_path / "a")), Atenea(),
                        Bauhaus(tmp_path / "s"), Revisor())
    assert exp.estado == "archivado", exp.revision["observaciones"]
    assert exp.diseno["imagenes"][0]["fuente"] == "Foto propia"
    assert sum(len(p.images) for p in PdfReader(exp.archivos["pdf"]).pages) >= 5   # 4 imágenes + logo
    assert "Logo institucional incluido." in exp.revision["comprobaciones"]
