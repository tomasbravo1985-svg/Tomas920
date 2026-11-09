"""BANCO DE RECURSOS VISUALES: fotografías, mapas, ilustraciones y el logo.

Cómo funciona (explicado simple):
- Cada imagen tiene una FICHA en recursos/catalogo.json: qué muestra, de dónde
  viene (fuente y licencia) y si ya está disponible o la estamos esperando.
- Las guías piden imágenes por su NOMBRE CORTO (id), por ejemplo "desierto_atacama".
- Si una imagen falta, queda "pendiente" y aparece en recursos/entrada/PEDIDO_DE_IMAGENES.md.
- El profesor deja la foto en recursos/entrada/ con ese nombre (desierto_atacama.jpg)
  y ejecuta:  python recursos.py importar
- Los archivos del profesor NUNCA se mueven, borran ni sobrescriben: se COPIAN.
"""
from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

from PIL import Image, ImageOps, ImageStat

from .configuracion import RAIZ

CARPETA = RAIZ / "recursos"
CATALOGO = CARPETA / "catalogo.json"
ENTRADA = CARPETA / "entrada"
IMAGENES = CARPETA / "imagenes"
LOGO = CARPETA / "logo" / "logo_escuela.png"
PEDIDO = ENTRADA / "PEDIDO_DE_IMAGENES.md"

TIPOS = ("fotografia", "mapa", "ilustracion", "ilustracion_generada", "grafico", "documento_historico")
EXTENSIONES = (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp")

# Calidad mínima para imprimir bien
DPI_MINIMO = 150          # puntos por pulgada al tamaño impreso
CONTRASTE_MINIMO = 35     # desviación de grises (0-127); menos = foto "lavada" en B/N


# ------------------------------------------------------------------ catálogo
def cargar() -> dict:
    if CATALOGO.is_file():
        return json.loads(CATALOGO.read_text(encoding="utf-8"))
    return {}


def guardar(catalogo: dict) -> None:
    CATALOGO.parent.mkdir(parents=True, exist_ok=True)
    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8")


def ficha(id_: str) -> dict | None:
    return cargar().get(id_)


def ruta_de(id_: str) -> Path | None:
    """Ruta del archivo de un recurso disponible (o None si no está)."""
    f = ficha(id_)
    if f and f.get("archivo") and (RAIZ / f["archivo"]).is_file():
        return RAIZ / f["archivo"]
    return None


def pedir(id_: str, tipo: str, descripcion: str, sugerencia: str = "", guia: str = "") -> dict:
    """Registra que una guía necesita una imagen que todavía no tenemos."""
    catalogo = cargar()
    f = catalogo.get(id_)
    if f is None:
        f = {"id": id_, "tipo": tipo, "descripcion": descripcion, "estado": "pendiente",
             "sugerencia_fuente": sugerencia, "fuente": "", "licencia": "", "autor": "",
             "archivo": "", "usado_en": []}
        catalogo[id_] = f
    if guia and guia not in f["usado_en"]:
        f["usado_en"].append(guia)
    guardar(catalogo)
    escribir_pedido()
    return f


def registrar(origen: Path, id_: str, tipo: str, descripcion: str = "", fuente: str = "",
              licencia: str = "", autor: str = "") -> dict:
    """COPIA una imagen al banco y le crea (o completa) su ficha. No toca el original."""
    origen = Path(origen)
    if origen.suffix.lower() not in EXTENSIONES:
        raise ValueError(f"Formato no aceptado: {origen.suffix}. Usa PNG o JPG.")
    if tipo not in TIPOS:
        raise ValueError(f"Tipo desconocido: {tipo}. Opciones: {', '.join(TIPOS)}")
    Image.open(origen).verify()  # comprueba que no esté dañada

    IMAGENES.mkdir(parents=True, exist_ok=True)
    destino = IMAGENES / f"{id_}{origen.suffix.lower()}"
    version = 2
    while destino.exists():   # nunca sobrescribir
        destino = IMAGENES / f"{id_}_v{version}{origen.suffix.lower()}"
        version += 1
    shutil.copy2(origen, destino)

    catalogo = cargar()
    f = catalogo.get(id_, {"id": id_, "usado_en": []})
    f.update({
        "tipo": tipo,
        "descripcion": descripcion or f.get("descripcion", ""),
        "fuente": fuente or f.get("fuente", ""),
        "licencia": licencia or f.get("licencia", ""),
        "autor": autor or f.get("autor", ""),
        "archivo": str(destino.relative_to(RAIZ)) if destino.is_relative_to(RAIZ) else str(destino),
        "estado": "provisoria" if tipo == "ilustracion_generada" else "disponible",
        "fecha_ingreso": date.today().isoformat(),
    })
    f.setdefault("sugerencia_fuente", "")
    catalogo[id_] = f
    guardar(catalogo)
    escribir_pedido()
    return f


def importar_entrada() -> list[str]:
    """Busca en recursos/entrada/ fotos con el nombre de un recurso pendiente y las incorpora."""
    ENTRADA.mkdir(parents=True, exist_ok=True)
    catalogo = cargar()
    importados = []
    for archivo in sorted(ENTRADA.iterdir()):
        if archivo.suffix.lower() not in EXTENSIONES:
            continue
        id_ = archivo.stem
        f = catalogo.get(id_)
        if f is None or f.get("estado") == "disponible":
            continue
        registrar(archivo, id_, f.get("tipo") if f.get("tipo") != "ilustracion_generada" else "fotografia",
                  f.get("descripcion", ""), fuente="Aportada por el profesor (completar fuente)")
        importados.append(id_)
    return importados


def pendientes() -> list[dict]:
    return [f for f in cargar().values() if f.get("estado") in ("pendiente", "provisoria")]


def escribir_pedido() -> None:
    """Escribe la lista de imágenes que faltan, en lenguaje sencillo, para el profesor."""
    faltan = pendientes()
    ENTRADA.mkdir(parents=True, exist_ok=True)
    lineas = ["# Imágenes que necesito", "",
              "Deja cada imagen en esta carpeta (`recursos/entrada/`) con el **nombre exacto** indicado",
              "(puede ser .jpg o .png) y luego ejecuta: `python recursos.py importar`.", "",
              "Recomendaciones: fotos nítidas, de al menos 1200 píxeles de ancho, con buen contraste",
              "(se imprimirán en blanco y negro). Anota de dónde salió cada imagen.", ""]
    if not faltan:
        lineas.append("✅ No falta ninguna imagen.")
    for f in faltan:
        estado = "provisoria (dibujo hecho por código: conviene reemplazarla)" if f["estado"] == "provisoria" else "FALTA"
        lineas += [f"## {f['id']}.jpg  —  {estado}",
                   f"- Qué debe mostrar: {f.get('descripcion', '')}",
                   f"- Tipo: {'fotografía o ilustración real' if f.get('tipo') == 'ilustracion_generada' else f.get('tipo', '')}"]
        if f.get("sugerencia_fuente"):
            lineas.append(f"- Dónde buscarla: {f['sugerencia_fuente']}")
        if f.get("usado_en"):
            lineas.append(f"- Se usa en: {', '.join(f['usado_en'])}")
        lineas.append("")
    PEDIDO.write_text("\n".join(lineas), encoding="utf-8")


# ------------------------------------------------------------------ calidad
def evaluar_calidad(ruta: Path, ancho_impreso_cm: float) -> dict:
    """Mide si la imagen se imprimirá bien en blanco y negro al tamaño indicado."""
    with Image.open(ruta) as im:
        ancho_px, alto_px = im.size
        gris = ImageOps.grayscale(im)
        contraste = ImageStat.Stat(gris).stddev[0]
    dpi = ancho_px / (ancho_impreso_cm / 2.54)
    problemas = []
    if dpi < DPI_MINIMO:
        problemas.append(f"resolución baja ({ancho_px} px de ancho; se verá borrosa al imprimir)")
    if contraste < CONTRASTE_MINIMO:
        problemas.append("poco contraste: en blanco y negro se verá gris y plana")
    proporcion = ancho_px / alto_px
    if proporcion > 3 or proporcion < 0.33:
        problemas.append("forma muy alargada; puede verse pequeña")
    return {"ancho_px": ancho_px, "alto_px": alto_px, "dpi": round(dpi), "contraste": round(contraste, 1),
            "problemas": problemas}


def preparar_para_imprimir(ruta: Path, destino_carpeta: Path) -> Path:
    """Copia en escala de grises con contraste ajustado (el original no se toca)."""
    destino_carpeta.mkdir(parents=True, exist_ok=True)
    destino = destino_carpeta / (ruta.stem + "_gris.png")
    with Image.open(ruta) as im:
        if im.mode in ("RGBA", "LA", "P"):
            fondo = Image.new("RGB", im.size, "white")
            im = im.convert("RGBA")
            fondo.paste(im, mask=im.split()[-1])
            im = fondo
        gris = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
        if gris.width > 2000:
            gris = gris.resize((2000, round(gris.height * 2000 / gris.width)))
        gris.save(destino)
    return destino


# ------------------------------------------------------------------ logo
def registrar_logo(origen: Path) -> dict:
    """Guarda el logo UNA vez; todas las guías lo usarán solas.
    Si ya había un logo, el anterior se conserva con otro nombre."""
    origen = Path(origen)
    if origen.suffix.lower() not in EXTENSIONES:
        raise ValueError("El logo debe ser PNG o JPG.")
    with Image.open(origen) as im:
        im.load()
        LOGO.parent.mkdir(parents=True, exist_ok=True)
        if LOGO.exists():
            anterior = LOGO.with_name(f"logo_anterior_{date.today().isoformat()}.png")
            n = 2
            while anterior.exists():
                anterior = LOGO.with_name(f"logo_anterior_{date.today().isoformat()}_{n}.png")
                n += 1
            shutil.copy2(LOGO, anterior)
        im.convert("RGBA").save(LOGO)
    return evaluar_calidad(LOGO, ancho_impreso_cm=2.6)


def logo_disponible() -> Path | None:
    return LOGO if LOGO.is_file() else None
