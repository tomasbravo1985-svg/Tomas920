"""BAUHAUS — DISEÑO.

Recibe: exp.contenido (de ATENEA).
Entrega:
- exp.diseno   = {"sopa": ..., "crucigrama": ..., "imagenes": [...], "logo": ...}
- exp.archivos = {"docx", "pdf", "solucionario_docx", "solucionario_pdf"}

Responsabilidades:
- Aplicar el formato institucional (config/escuela.toml y config/formato_guia.toml).
- Tamaño carta, vertical, espacios amplios para escribir.
- Generar sopas de letras y crucigramas CON su solución (en un solucionario aparte).
- Usar fotografías, mapas e ilustraciones del BANCO DE RECURSOS (recursos/catalogo.json).
  Si falta una imagen, la pide al profesor (recursos/entrada/PEDIDO_DE_IMAGENES.md).
- Usar automáticamente el logo guardado una vez (recursos/logo/logo_escuela.png).
- Imágenes en escala de grises, con contraste ajustado para impresión.
- Exportar Word (python-docx) y PDF (LibreOffice, gratuito).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.shared import Cm, Pt, RGBColor

from .. import configuracion, cuadriculas, memoria, recursos
from .. import word as w
from ..configuracion import RAIZ
from ..expediente import Expediente
from .base import Agente

LETRAS = "ABCD"
ANCHO_UTIL_CM = 21.59 - 2 * 1.8   # carta menos márgenes
ANCHO_IMAGEN_CM = (ANCHO_UTIL_CM - 0.6) / 2 - 1.2   # 2 imágenes por fila
ANCHO_LOGO_CM = 2.6
FUENTE = "Arial"


def slug(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Za-z0-9]+", "_", texto).strip("_")


def nombre_corto(asignatura: str) -> str:
    """'Historia, Geografía y Ciencias Sociales' -> 'Historia'."""
    return slug(asignatura.split(",")[0])


def buscar_libreoffice() -> str | None:
    for nombre in ("soffice", "libreoffice"):
        if shutil.which(nombre):
            return shutil.which(nombre)
    for ruta in (r"C:\Program Files\LibreOffice\program\soffice.exe",
                 r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                 "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if os.path.exists(ruta):
            return ruta
    return None


def convertir_a_pdf(docx: Path) -> Path | None:
    soffice = buscar_libreoffice()
    if not soffice:
        return None
    with tempfile.TemporaryDirectory() as perfil:
        subprocess.run(
            [soffice, f"-env:UserInstallation=file://{Path(perfil).as_posix()}",
             "--headless", "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)],
            check=False, capture_output=True, timeout=180)
    pdf = docx.with_suffix(".pdf")
    return pdf if pdf.exists() else None


class Bauhaus(Agente):
    nombre = "bauhaus"

    def __init__(self, carpeta_salida: Path | None = None):
        self.carpeta_salida = Path(carpeta_salida) if carpeta_salida else RAIZ / "salida"
        self.escuela = configuracion.leer("escuela")
        self.formato = configuracion.leer("formato_guia")

    # ------------------------------------------------------------------ trabajo
    def trabajar(self, exp: Expediente) -> Expediente:
        c = exp.contenido
        faltan = [x["id"] for x in self.formato["secciones"] if not c.get(x["id"])]
        if faltan:  # no se diseña una guía incompleta: REVISOR explicará qué falta
            exp.diseno, exp.archivos = {}, {}
            exp.anotar("bauhaus", "revisor", "aviso", f"No diseñé: faltan secciones {', '.join(faltan)}.")
            return exp
        semilla = 7 + 31 * exp.intentos_correccion   # si hay que rehacer, cambia el azar
        self.reglas = memoria.reglas(exp.lecciones)
        e = exp.encargo
        carpeta = self.carpeta_salida / f"{e.fecha}_{nombre_corto(e.asignatura)}_{slug('_'.join(e.cursos))}_guia{e.numero}"
        carpeta.mkdir(parents=True, exist_ok=True)
        self.carpeta_imagenes = carpeta / "_imagenes_impresion"
        exp.diseno = {
            "sopa": self._sopa(c["sopa_de_letras"]["palabras"], semilla),
            "crucigrama": cuadriculas.crear_crucigrama(c["crucigrama"]["pistas"], semilla=semilla),
            "imagenes": self._resolver_imagenes(exp, c["analisis_imagenes"].get("imagenes", [])),
            "logo": str(recursos.logo_disponible() or ""),
        }
        base = f"{nombre_corto(e.asignatura)}_{slug('_'.join(e.cursos))}_guia{e.numero}_{e.fecha}"

        guia = carpeta / f"{base}.docx"
        self._documento_guia(exp, carpeta).save(guia)
        solucionario = carpeta / f"{base}_SOLUCIONARIO.docx"
        self._documento_solucionario(exp).save(solucionario)

        exp.archivos = {"carpeta": str(carpeta), "docx": str(guia), "solucionario_docx": str(solucionario)}
        for clave, docx in (("pdf", guia), ("solucionario_pdf", solucionario)):
            pdf = convertir_a_pdf(docx)
            if pdf:
                exp.archivos[clave] = str(pdf)

        exp.cambiar_estado("disenado")
        exp.anotar("bauhaus", "revisor", "entrega",
                   f"Guía diseñada en {carpeta.name} (PDF: {'sí' if 'pdf' in exp.archivos else 'no'}).")
        return exp

    def _resolver_imagenes(self, exp, imagenes) -> list[dict]:
        """Busca cada imagen en el banco de recursos. Si falta, la pide al profesor."""
        guia = f"{exp.encargo.asignatura} {', '.join(exp.encargo.cursos)} guía {exp.encargo.numero}"
        resueltas = []
        for img in imagenes:
            id_ = img.get("recurso") or Path(img.get("archivo", "")).stem
            ruta = recursos.ruta_de(id_)
            if ruta is None and img.get("archivo") and (RAIZ / img["archivo"]).is_file():
                ruta = RAIZ / img["archivo"]
            ficha = recursos.ficha(id_) or {}
            if ruta is None:
                ficha = recursos.pedir(id_, img.get("tipo", "fotografia"),
                                       img.get("descripcion", "") or img.get("pie", ""),
                                       img.get("sugerencia_fuente", ""), guia)
            resueltas.append({
                "id": id_, "pie": img.get("pie", ""), "ruta": str(ruta) if ruta else "",
                "tipo": ficha.get("tipo", img.get("tipo", "")),
                "estado": "falta" if ruta is None else ficha.get("estado", "disponible"),
                "descripcion": ficha.get("descripcion") or img.get("descripcion", ""),
                "fuente": ficha.get("fuente", ""), "licencia": ficha.get("licencia", ""),
                "ancho_cm": round(ANCHO_IMAGEN_CM, 1),
                "calidad": recursos.evaluar_calidad(ruta, ANCHO_IMAGEN_CM) if ruta else None,
            })
        return resueltas

    def _sopa(self, palabras, semilla):
        largo = max(len(cuadriculas.normalizar(p)) for p in palabras)
        for tamano in range(max(13, largo + 2), 19):
            try:
                return cuadriculas.crear_sopa(palabras, tamano=tamano, semilla=semilla)
            except ValueError:
                continue
        raise ValueError("Las palabras de la sopa no caben ni en 18x18.")

    # ------------------------------------------------------------------ base del documento
    def _documento_base(self, exp: Expediente, titulo_extra: str = "") -> Document:
        doc = Document()
        estilo = doc.styles["Normal"]
        estilo.font.name = FUENTE
        estilo.font.size = Pt(12)
        estilo.element.rPr.rFonts.set(w.qn("w:eastAsia"), FUENTE)
        estilo.paragraph_format.space_after = Pt(4)

        sec = doc.sections[0]
        sec.page_width, sec.page_height = Cm(21.59), Cm(27.94)
        sec.orientation = WD_ORIENT.PORTRAIT
        sec.left_margin = sec.right_margin = Cm(1.8)
        sec.top_margin, sec.bottom_margin = Cm(1.5), Cm(1.5)
        sec.header_distance = sec.footer_distance = Cm(0.8)

        e = exp.encargo
        cab = sec.header.paragraphs[0]
        cab.text = f"{self.escuela['escuela']['nombre']} · {e.asignatura} · {', '.join(e.cursos)}{titulo_extra}"
        cab.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for r in cab.runs:
            r.font.size = Pt(8)
            r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

        pie = sec.footer.paragraphs[0]
        pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pie.add_run("Página ")
        w.campo(pie, "PAGE")
        pie.add_run(" de ")
        w.campo(pie, "NUMPAGES")
        for r in pie.runs:
            r.font.size = Pt(9)
        return doc

    def _encabezado_institucional(self, doc, exp: Expediente):
        esc = self.escuela["escuela"]
        tabla = doc.add_table(rows=1, cols=2)
        w.sin_bordes_tabla(tabla)
        w.ancho_columnas(tabla, [3.2, ANCHO_UTIL_CM - 3.2])
        celda_logo, celda_texto = tabla.rows[0].cells
        logo = recursos.logo_disponible()   # se guarda una vez y se usa en todas las guías
        if logo:
            celda_logo.paragraphs[0].add_run().add_picture(
                str(recursos.preparar_para_imprimir(logo, self.carpeta_imagenes)), width=Cm(ANCHO_LOGO_CM))
        else:
            w.bordes_celda(celda_logo, color="808080", estilo="dashed")
            p = celda_logo.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run("\nLOGO\n")
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
        celda_texto.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = celda_texto.paragraphs[0]
        r = p.add_run(esc["nombre"].upper())
        r.bold = True
        r.font.size = Pt(15)
        p2 = celda_texto.add_paragraph(f"Comuna de {esc['comuna']} · {esc['region']}")
        p2.runs[0].font.size = Pt(10)
        p3 = celda_texto.add_paragraph(f"{exp.encargo.asignatura} · {', '.join(exp.encargo.cursos)}")
        p3.runs[0].font.size = Pt(10)
        p3.runs[0].bold = True
        docente = self.escuela.get("docente", {}).get("nombre", "")
        if docente:
            p4 = celda_texto.add_paragraph(f"Docente: {docente}")
            p4.runs[0].font.size = Pt(10)

    def _titulo(self, doc, texto, tamano=18):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(10)
        r = p.add_run(texto)
        r.bold = True
        r.font.size = Pt(tamano)

    def _datos_estudiante(self, doc):
        tabla = doc.add_table(rows=1, cols=3)
        w.sin_bordes_tabla(tabla)
        w.ancho_columnas(tabla, [9.5, 3.5, ANCHO_UTIL_CM - 13])
        for celda, campo_ in zip(tabla.rows[0].cells, self.formato["encabezado"]["campos"]):
            w.bordes_celda(celda, lados=("bottom",), grosor=6)
            r = celda.paragraphs[0].add_run(f"{campo_}:")
            r.bold = True
        w.alto_fila(tabla.rows[0], 1.0)

    def _recuadro(self, doc, lineas: list[tuple[str, str]], gris="F2F2F2"):
        tabla = doc.add_table(rows=1, cols=1)
        w.ancho_columnas(tabla, [ANCHO_UTIL_CM])
        celda = tabla.rows[0].cells[0]
        w.bordes_celda(celda, grosor=6)
        w.sombrear(celda, gris)
        primero = True
        for etiqueta, texto in lineas:
            p = celda.paragraphs[0] if primero else celda.add_paragraph()
            primero = False
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(f"{etiqueta} ")
            r.bold = True
            r.font.size = Pt(10.5)
            r2 = p.add_run(texto)
            r2.font.size = Pt(10.5)
        doc.add_paragraph()

    def _barra(self, doc, numero, titulo, salto_pagina=False):
        if salto_pagina:
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(6)
        w.sombrear(p, "BFBFBF")
        etiqueta = f"  ACTIVIDAD {numero}  │  " if numero else "  "
        r = p.add_run(f"{etiqueta}{titulo.upper()}")
        r.bold = True
        r.font.size = Pt(13)
        w.no_separar_de_lo_siguiente(p)

    def _instruccion(self, doc, texto):
        p = doc.add_paragraph()
        r = p.add_run("Instrucción: ")
        r.bold = True
        p.add_run(texto).italic = True
        w.no_separar_de_lo_siguiente(p)

    def _preguntas(self, doc, preguntas, inicio=1):
        for i, preg in enumerate(preguntas, start=inicio):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.add_run(f"{i}. ").bold = True
            p.add_run(preg["texto"])
            w.no_separar_de_lo_siguiente(p)
            minimo = getattr(self, "reglas", {}).get("min_lineas_respuesta", 0) or 0
            for _ in range(max(preg.get("lineas", 3), minimo)):
                w.linea_para_escribir(doc)

    # ------------------------------------------------------------------ guía del estudiante
    def _documento_guia(self, exp: Expediente, carpeta: Path) -> Document:
        c = exp.contenido
        doc = self._documento_base(exp)
        self._encabezado_institucional(doc, exp)
        self._titulo(doc, c["titulo"])
        n = exp.encargo.numero
        p = doc.add_paragraph(f"Guía N.º {n} · Duración: {exp.encargo.duracion_minutos} minutos")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._datos_estudiante(doc)
        doc.add_paragraph()
        self._recuadro(doc, [("Objetivo:", c["objetivo"])])

        secciones = {s["id"]: s for s in self.formato["secciones"]}
        num = 0

        def siguiente():
            nonlocal num
            num += 1
            return num

        # 1. Actividad inicial
        ai = c["actividad_inicial"]
        self._barra(doc, siguiente(), secciones["actividad_inicial"]["titulo"])
        self._instruccion(doc, ai["instruccion"])
        self._preguntas(doc, ai["preguntas"])

        # 2. Sopa de letras
        self._barra(doc, siguiente(), secciones["sopa_de_letras"]["titulo"], salto_pagina=True)
        self._instruccion(doc, c["sopa_de_letras"]["instruccion"])
        self._grilla_sopa(doc, exp.diseno["sopa"], solucion=False)
        self._lista_palabras(doc, c["sopa_de_letras"]["palabras"])

        # 3. Crucigrama
        self._barra(doc, siguiente(), secciones["crucigrama"]["titulo"], salto_pagina=True)
        self._instruccion(doc, c["crucigrama"]["instruccion"])
        self._grilla_crucigrama(doc, exp.diseno["crucigrama"], solucion=False)
        self._pistas_crucigrama(doc, exp.diseno["crucigrama"])

        # 4. Lectura
        lec = c["lectura"]
        self._barra(doc, siguiente(), secciones["lectura"]["titulo"], salto_pagina=True)
        t = doc.add_paragraph()
        t.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = t.add_run(lec["titulo"])
        r.bold = True
        r.font.size = Pt(14)
        for parrafo in lec["parrafos"]:
            p = doc.add_paragraph(parrafo)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.2
            p.paragraph_format.space_after = Pt(6)
        sub = doc.add_paragraph()
        sub.add_run("Responde según la lectura:").bold = True
        w.no_separar_de_lo_siguiente(sub)
        self._preguntas(doc, lec["preguntas"])

        # 5. Análisis de imágenes
        ai = c["analisis_imagenes"]
        self._barra(doc, siguiente(), secciones["analisis_imagenes"]["titulo"])
        self._instruccion(doc, ai["instruccion"])
        self._imagenes(doc, exp.diseno["imagenes"])
        if ai.get("tabla"):
            self._tabla_para_completar(doc, ai["tabla"])
        if ai.get("preguntas"):
            self._preguntas(doc, ai["preguntas"])

        # 6. Selección única
        su = c["seleccion_unica"]
        self._barra(doc, siguiente(), secciones["seleccion_unica"]["titulo"])
        self._instruccion(doc, su["instruccion"])
        for i, preg in enumerate(su["preguntas"], start=1):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.add_run(f"{i}. ").bold = True
            p.add_run(preg["texto"])
            w.no_separar_de_lo_siguiente(p)
            for letra, alt in zip(LETRAS, preg["alternativas"]):
                pa = doc.add_paragraph(f"{letra})  {alt}")
                pa.paragraph_format.left_indent = Cm(0.8)
                pa.paragraph_format.space_after = Pt(1)
                if letra != "D":
                    w.no_separar_de_lo_siguiente(pa)

        # 7. Verdadero o falso
        vf = c["verdadero_falso"]
        self._barra(doc, siguiente(), secciones["verdadero_falso"]["titulo"])
        self._instruccion(doc, vf["instruccion"])
        tabla = doc.add_table(rows=len(vf["afirmaciones"]), cols=2)
        w.bordes_tabla(tabla, color="808080")
        w.ancho_columnas(tabla, [1.6, ANCHO_UTIL_CM - 1.6])
        for fila, af in zip(tabla.rows, vf["afirmaciones"]):
            w.alto_fila(fila, 1.1)
            fila.cells[1].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            fila.cells[1].paragraphs[0].add_run(af["texto"])
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.add_run("Corrige aquí las afirmaciones falsas:").bold = True
        w.no_separar_de_lo_siguiente(p)
        for _ in range(sum(1 for a in vf["afirmaciones"] if not a["respuesta"])):
            w.linea_para_escribir(doc)

        # 8. Aplicación
        ap = c["aplicacion"]
        titulo_ap = secciones["aplicacion"]["titulo"] + (f": {ap['titulo']}" if ap.get("titulo") else "")
        self._barra(doc, siguiente(), titulo_ap, salto_pagina=True)
        self._instruccion(doc, ap["instruccion"])
        for i, paso in enumerate(ap.get("pasos", []), start=1):
            pp = doc.add_paragraph(f"Paso {i}: {paso}")
            pp.paragraph_format.left_indent = Cm(0.5)
        if ap.get("recuadro_dibujo"):
            tabla = doc.add_table(rows=1, cols=1)
            w.ancho_columnas(tabla, [ANCHO_UTIL_CM])
            w.bordes_tabla(tabla, grosor=12)
            w.alto_fila(tabla.rows[0], 5.5)
        for _ in range(ap.get("lineas", 6)):
            w.linea_para_escribir(doc)

        # 9. Ticket de salida
        ts = c["ticket_salida"]
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        w.no_separar_de_lo_siguiente(p)
        p.add_run("✂ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -").font.color.rgb = RGBColor(0x80, 0x80, 0x80)
        tabla = doc.add_table(rows=1, cols=1)
        w.ancho_columnas(tabla, [ANCHO_UTIL_CM])
        w.no_dividir_fila(tabla.rows[0])
        celda = tabla.rows[0].cells[0]
        w.bordes_celda(celda, grosor=12, estilo="dashed")
        cp = celda.paragraphs[0]
        r = cp.add_run(secciones["ticket_salida"]["titulo"].upper())
        r.bold = True
        r.font.size = Pt(13)
        celda.add_paragraph("Nombre: ______________________________   Curso: ________")
        for i, preg in enumerate(ts["preguntas"], start=1):
            pq = celda.add_paragraph()
            pq.paragraph_format.space_before = Pt(3)
            pq.add_run(f"{i}. ").bold = True
            pq.add_run(preg["texto"])
            for _ in range(preg.get("lineas", 2)):
                w.linea_para_escribir(celda, alto_cm=0.8)
        if ts.get("autoevaluacion"):
            pa = celda.add_paragraph()
            pa.paragraph_format.space_before = Pt(8)
            pa.add_run(ts["autoevaluacion"]).bold = True
        return doc

    # ------------------------------------------------------------------ piezas
    def _grilla_sopa(self, doc, sopa, solucion: bool):
        grilla = sopa["grilla"]
        n = len(grilla)
        lado = min(1.05, (ANCHO_UTIL_CM - 1) / n)
        marcadas = set()
        if solucion:
            for u in sopa["ubicaciones"]:
                df, dc = cuadriculas.DIRECCIONES_SOPA[u["direccion"]]
                for i in range(len(u["palabra"])):
                    marcadas.add((u["fila"] + df * i, u["col"] + dc * i))
        tabla = doc.add_table(rows=n, cols=n)
        tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
        w.bordes_tabla(tabla, color="808080", grosor=4)
        w.ancho_columnas(tabla, [lado] * n)
        for f, fila in enumerate(tabla.rows):
            w.alto_fila(fila, lado)
            for col, celda in enumerate(fila.cells):
                celda.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                w.margenes_celda(celda, 0)
                p = celda.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_after = Pt(0)
                r = p.add_run(grilla[f][col])
                r.font.size = Pt(14 if lado > 0.95 else 12)
                if (f, col) in marcadas:
                    r.bold = True
                    w.sombrear(celda, "BFBFBF")
        doc.add_paragraph()

    def _lista_palabras(self, doc, palabras):
        p = doc.add_paragraph()
        p.add_run("Palabras para buscar:").bold = True
        cols = 3
        filas = -(-len(palabras) // cols)
        tabla = doc.add_table(rows=filas, cols=cols)
        w.sin_bordes_tabla(tabla)
        w.ancho_columnas(tabla, [ANCHO_UTIL_CM / cols] * cols)
        for i, palabra in enumerate(palabras):
            celda = tabla.rows[i % filas].cells[i // filas]
            celda.paragraphs[0].add_run(f"☐  {cuadriculas.normalizar(palabra)}").font.size = Pt(12)

    def _grilla_crucigrama(self, doc, cruci, solucion: bool):
        grilla = cruci["grilla"]
        alto, ancho = cruci["alto"], cruci["ancho"]
        lado = min(0.85, (ANCHO_UTIL_CM - 0.5) / ancho, 12.5 / alto)
        numeros = {(p["fila"], p["col"]): p["numero"] for p in cruci["palabras"]}
        tabla = doc.add_table(rows=alto, cols=ancho)
        tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
        w.sin_bordes_tabla(tabla)
        w.ancho_columnas(tabla, [lado] * ancho)
        for f, fila in enumerate(tabla.rows):
            w.alto_fila(fila, lado)
            for col, celda in enumerate(fila.cells):
                w.margenes_celda(celda, 0.03)
                if not grilla[f][col]:
                    continue
                w.bordes_celda(celda, grosor=10)
                p = celda.paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 0.8
                if (f, col) in numeros:
                    r = p.add_run(str(numeros[(f, col)]))
                    r.font.size = Pt(7)
                    r.bold = True
                if solucion:
                    p2 = celda.add_paragraph() if (f, col) in numeros else p
                    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p2.paragraph_format.space_after = Pt(0)
                    p2.paragraph_format.line_spacing = 0.8
                    r = p2.add_run(grilla[f][col])
                    r.font.size = Pt(10)
                    r.bold = True
        doc.add_paragraph()

    def _pistas_crucigrama(self, doc, cruci):
        for direccion, nombre in (("H", "Horizontales →"), ("V", "Verticales ↓")):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.add_run(nombre).bold = True
            w.no_separar_de_lo_siguiente(p)
            for pal in cruci["palabras"]:
                if pal["direccion"] == direccion:
                    q = doc.add_paragraph()
                    q.paragraph_format.left_indent = Cm(0.5)
                    q.paragraph_format.space_after = Pt(2)
                    q.add_run(f"{pal['numero']}. ").bold = True
                    q.add_run(f"{pal['pista']} ({len(pal['palabra'])} letras)")

    def _imagenes(self, doc, imagenes):
        cols = 2
        filas = -(-len(imagenes) // cols)
        tabla = doc.add_table(rows=filas, cols=cols)
        tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
        w.sin_bordes_tabla(tabla)
        ancho = (ANCHO_UTIL_CM - 0.6) / cols
        w.ancho_columnas(tabla, [ancho] * cols)
        for fila in tabla.rows:
            w.no_dividir_fila(fila)
        for i, img in enumerate(imagenes):
            celda = tabla.rows[i // cols].cells[i % cols]
            p = celda.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if img["ruta"]:
                impresion = recursos.preparar_para_imprimir(Path(img["ruta"]), self.carpeta_imagenes)
                p.add_run().add_picture(str(impresion), width=Cm(ANCHO_IMAGEN_CM))
            else:  # falta: queda un recuadro visible y REVISOR detendrá la entrega
                w.bordes_celda(celda, estilo="dashed", color="808080")
                p.add_run(f"\n\n[FALTA IMAGEN: {img['id']}]\n{img['descripcion']}\n\n").italic = True
            pie = celda.add_paragraph(img.get("pie", ""))
            pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pie.runs[0].bold = True
            if img.get("fuente"):
                credito = celda.add_paragraph(f"Fuente: {img['fuente']}" + (f" ({img['licencia']})" if img.get("licencia") else ""))
                credito.alignment = WD_ALIGN_PARAGRAPH.CENTER
                credito.runs[0].font.size = Pt(7)
        doc.add_paragraph()

    def _tabla_para_completar(self, doc, tabla_def):
        columnas, filas = tabla_def["columnas"], tabla_def["filas"]
        tabla = doc.add_table(rows=len(filas) + 1, cols=len(columnas))
        w.bordes_tabla(tabla)
        primera = 2.0
        resto = (ANCHO_UTIL_CM - primera) / (len(columnas) - 1)
        w.ancho_columnas(tabla, [primera] + [resto] * (len(columnas) - 1))
        for celda, titulo in zip(tabla.rows[0].cells, columnas):
            w.sombrear(celda, "D9D9D9")
            r = celda.paragraphs[0].add_run(titulo)
            r.bold = True
            r.font.size = Pt(10)
        w.no_dividir_fila(tabla.rows[0])
        tabla.rows[0]._tr.get_or_add_trPr().append(w._elemento("w:tblHeader"))  # se repite si cambia de página
        for fila, etiqueta in zip(tabla.rows[1:], filas):
            w.alto_fila(fila, 1.8)
            r = fila.cells[0].paragraphs[0].add_run(etiqueta)
            r.bold = True
        doc.add_paragraph()

    # ------------------------------------------------------------------ solucionario
    def _documento_solucionario(self, exp: Expediente) -> Document:
        c = exp.contenido
        doc = self._documento_base(exp, " · SOLUCIONARIO (uso docente)")
        self._titulo(doc, f"SOLUCIONARIO — {c['titulo']}", 16)
        datos = [("Asignatura:", exp.encargo.asignatura), ("Curso:", ", ".join(exp.encargo.cursos)),
                 ("Objetivo:", c["objetivo"])]
        for oa in c.get("oa_verificacion", []):
            if oa["estado"] == "verificado":
                datos.append((f"{oa['codigo']} (verificado):", f"{oa['texto']}  [Fuente: {oa['fuente']}]"))
            elif oa["estado"] == "institucional":
                datos.append(("Objetivo de Aprendizaje:", oa["motivo"]))
            else:
                datos.append(("Objetivo de Aprendizaje: PENDIENTE DE CONFIRMACIÓN.",
                              f"{oa['motivo']} Propuesta sin verificar: {oa['texto'] or '—'}"))
        if c.get("distribucion_tiempo"):
            datos.append(("Tiempo sugerido:", " · ".join(f"{k}: {v} min" for k, v in c["distribucion_tiempo"].items())))
        self._recuadro(doc, datos)

        self._barra(doc, None, "Sopa de letras (solución)")
        self._grilla_sopa(doc, exp.diseno["sopa"], solucion=True)

        self._barra(doc, None, "Crucigrama (solución)", salto_pagina=True)
        self._grilla_crucigrama(doc, exp.diseno["crucigrama"], solucion=True)
        for pal in exp.diseno["crucigrama"]["palabras"]:
            doc.add_paragraph(f"{pal['numero']} {'→' if pal['direccion'] == 'H' else '↓'}  {pal['palabra']}")

        self._barra(doc, None, "Respuestas", salto_pagina=True)
        p = doc.add_paragraph()
        p.add_run("Lectura:").bold = True
        for i, preg in enumerate(c["lectura"]["preguntas"], start=1):
            doc.add_paragraph(f"{i}. {preg.get('respuesta', 'Respuesta abierta.')}")
        if c["analisis_imagenes"].get("respuestas"):
            p = doc.add_paragraph()
            p.add_run("Análisis de imágenes:").bold = True
            for k, v in c["analisis_imagenes"]["respuestas"].items():
                doc.add_paragraph(f"{k}: {v}")
        p = doc.add_paragraph()
        p.add_run("Selección única:  ").bold = True
        p.add_run("   ".join(f"{i}-{q['correcta']}" for i, q in enumerate(c["seleccion_unica"]["preguntas"], 1)))
        p = doc.add_paragraph()
        p.add_run("Verdadero o falso:").bold = True
        for i, a in enumerate(c["verdadero_falso"]["afirmaciones"], start=1):
            texto = f"{i}. {'V' if a['respuesta'] else 'F'}"
            if not a["respuesta"] and a.get("correccion"):
                texto += f" — {a['correccion']}"
            doc.add_paragraph(texto)
        return doc
