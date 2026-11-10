"""Trae fotografías de Wikimedia Commons al banco de recursos, CON su autor y licencia.

Uso:
    python herramientas/wikimedia.py paisaje_desierto "File:Nombre_de_la_foto.jpg"

Reglas:
- Solo licencias libres que permiten adaptar la imagen (se convierte a gris):
  dominio público, CC0, CC BY y CC BY-SA. Se rechazan NC (no comercial) y ND (sin derivadas).
- Se guarda la fuente, el autor y la licencia; BAUHAUS imprime el crédito bajo la imagen.
- Se descarga una versión de 1920 px de ancho (tamaño estándar de Wikimedia, suficiente para imprimir nítido).
- Respeta los límites de Wikimedia: pocas solicitudes, espera y reintenta si responde 429.
"""
from __future__ import annotations

import html
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from giorgio import recursos  # noqa: E402

UA = "GIORGIO-GUIAS/0.1 (https://github.com/tomasbravo1985-svg/Tomas920; herramienta educativa escolar)"
LICENCIAS_LIBRES = ("public domain", "dominio público", "cc0", "cc by", "cc-by", "cc by-sa", "cc-by-sa", "pdm")
LICENCIAS_RECHAZADAS = ("nc", "nd")


def _get(url: str, intentos: int = 5) -> bytes:
    espera = 20
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == intentos - 1:
                raise
            time.sleep(espera)
            espera *= 2
    raise RuntimeError("sin respuesta")


def _limpio(t: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()


def ficha(nombre: str) -> dict:
    """Lee la página del archivo: dirección original, licencia, autor y tamaño."""
    if not nombre.startswith("File:"):
        nombre = "File:" + nombre
    pagina = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(nombre.replace(" ", "_"))
    h = _get(pagina).decode("utf-8", "replace").replace("&#95;", "_")
    orig = re.search(r'class="fullMedia".*?href="(https://upload\.wikimedia\.org/[^"]+)"', h, re.S)
    lic = re.search(r'class="licensetpl_short"[^>]*>(.*?)</span>', h, re.S)
    atr = re.search(r'class="licensetpl_attr"[^>]*>(.*?)</span>', h, re.S)
    aut = re.search(r'id="fileinfotpl_aut"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>', h, re.S)
    dims = re.search(r'Original file.*?\(([\d,\.]+)\s*×\s*([\d,\.]+)\s*pixels', h, re.S)
    autor = _limpio((atr or aut).group(1)) if (atr or aut) else ""
    autor = re.split(r"You are free|Usted es libre|Eres libre", autor)[0].strip()[:100]
    return {
        "archivo": nombre, "pagina": pagina,
        "original": html.unescape(orig.group(1)).split("?")[0] if orig else "",
        "licencia": _limpio(lic.group(1)) if lic else "",
        "autor": autor,
        "ancho": int(dims.group(1).replace(",", "").replace(".", "")) if dims else 0,
    }


def licencia_aceptable(licencia: str) -> bool:
    l = licencia.lower()
    partes = set(re.split(r"[\s\-]+", l))
    if partes & set(LICENCIAS_RECHAZADAS):
        return False
    return any(x in l for x in LICENCIAS_LIBRES)


def url_descarga(original: str, ancho_original: int, ancho: int = 1920) -> str:
    # Wikimedia solo entrega tamaños estándar (250, 330, 500, 960, 1280, 1920, 3840 px)
    if ancho_original and ancho_original <= ancho:
        return original
    m = re.match(r"(https://upload\.wikimedia\.org/wikipedia/commons)/(\w)/(\w\w)/(.+)$", original)
    if not m:
        return original
    return f"{m.group(1)}/thumb/{m.group(2)}/{m.group(3)}/{m.group(4)}/{ancho}px-{m.group(4)}"


def importar(id_recurso: str, nombre_archivo: str, descripcion: str = "") -> dict:
    f = ficha(nombre_archivo)
    if not f["original"]:
        raise ValueError(f"No encontré la imagen {nombre_archivo}.")
    if not licencia_aceptable(f["licencia"]):
        raise ValueError(f"Licencia no permitida para las guías: '{f['licencia']}'.")
    datos = _get(url_descarga(f["original"], f["ancho"]))
    with tempfile.TemporaryDirectory() as tmp:
        ext = Path(urllib.parse.urlparse(f["original"]).path).suffix.lower() or ".jpg"
        temporal = Path(tmp) / f"{id_recurso}{ext}"
        temporal.write_bytes(datos)
        anterior = recursos.ficha(id_recurso) or {}
        registrado = recursos.registrar(
            temporal, id_recurso, "fotografia",
            descripcion or anterior.get("descripcion", ""),
            fuente=f"Wikimedia Commons, {f['autor']}" if f["autor"] else "Wikimedia Commons",
            licencia=f["licencia"], autor=f["autor"])
    cat = recursos.cargar()
    cat[id_recurso]["pagina_fuente"] = f["pagina"]
    recursos.guardar(cat)
    recursos.escribir_creditos()
    return registrado | {"pagina_fuente": f["pagina"]}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(1)
    r = importar(sys.argv[1], sys.argv[2], " ".join(sys.argv[3:]))
    print(f"Importada {r['id']}: {r['archivo']}  [{r['licencia']}]  {r['fuente']}")
