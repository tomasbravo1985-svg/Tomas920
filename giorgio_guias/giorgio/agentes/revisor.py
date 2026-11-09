"""REVISOR — CALIDAD.

Recibe: exp.contenido + exp.diseno + exp.archivos.
Entrega: exp.revision = {
    "aprobada": True/False,
    "observaciones": [{"responsable": "atenea"|"bauhaus", "seccion": ..., "problema": ...}],
    "advertencias": [...],      # cosas que conviene mirar pero no impiden entregar
    "comprobaciones": [...],    # lo que se revisó y estaba bien
}

REVISOR no confía en los demás: vuelve a buscar cada palabra en la sopa,
lee el crucigrama letra por letra y cuenta las páginas del PDF.
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Cm

from .. import configuracion, cuadriculas
from ..expediente import Expediente
from .base import Agente

MINIMOS = {"sopa_palabras": 8, "crucigrama_pistas": 6, "lectura_parrafos": 3,
           "lectura_preguntas": 3, "seleccion_unica": 4, "verdadero_falso": 4}


class Revisor(Agente):
    nombre = "revisor"

    def __init__(self):
        self.formato = configuracion.leer("formato_guia")

    def trabajar(self, exp: Expediente) -> Expediente:
        self.obs, self.adv, self.ok = [], [], []
        c = exp.contenido
        completo = self._contenido(exp, c)
        if completo:
            self._cuadriculas(exp)
        self._documento(exp)

        exp.revision = {"aprobada": not self.obs, "observaciones": self.obs,
                        "advertencias": self.adv, "comprobaciones": self.ok}
        for o in self.obs:
            exp.anotar("revisor", o["responsable"], "solicitud_correccion",
                       f"[{o['seccion']}] {o['problema']}")
        if not self.obs:
            exp.anotar("revisor", "archivo", "entrega", "Guía aprobada.")
        return exp

    # ---------------------------------------------------------------- ayudas
    def _falla(self, quien, seccion, problema):
        self.obs.append({"responsable": quien, "seccion": seccion, "problema": problema})

    def _minimo(self, lista, minimo, seccion, que):
        if len(lista) < minimo:
            self._falla("atenea", seccion, f"Tiene {len(lista)} {que}; se necesitan al menos {minimo}.")
        else:
            self.ok.append(f"{seccion}: {len(lista)} {que}.")

    # ---------------------------------------------------------------- 1. contenido
    def _contenido(self, exp, c):
        for s in self.formato["secciones"]:
            if not c.get(s["id"]):
                self._falla("atenea", s["id"], "Falta esta sección.")
        if not c.get("objetivo"):
            self._falla("atenea", "objetivo", "Falta el objetivo de la clase.")
        if self.obs:
            return False
        self.ok.append("Están las 9 secciones obligatorias y el objetivo.")

        self._minimo(c["sopa_de_letras"].get("palabras", []), MINIMOS["sopa_palabras"], "sopa_de_letras", "palabras")
        pistas = c["crucigrama"].get("pistas", [])
        self._minimo(pistas, MINIMOS["crucigrama_pistas"], "crucigrama", "pistas")
        if any(not p.get("pista") for p in pistas):
            self._falla("atenea", "crucigrama", "Hay palabras sin pista.")
        self._minimo(c["lectura"].get("parrafos", []), MINIMOS["lectura_parrafos"], "lectura", "párrafos")
        self._minimo(c["lectura"].get("preguntas", []), MINIMOS["lectura_preguntas"], "lectura", "preguntas")
        if not c["analisis_imagenes"].get("imagenes"):
            self._falla("atenea", "analisis_imagenes", "No hay imágenes para analizar.")

        su = c["seleccion_unica"].get("preguntas", [])
        self._minimo(su, MINIMOS["seleccion_unica"], "seleccion_unica", "preguntas")
        for i, q in enumerate(su, 1):
            if len(q.get("alternativas", [])) != 4:
                self._falla("atenea", "seleccion_unica", f"La pregunta {i} no tiene exactamente 4 alternativas.")
            if q.get("correcta") not in ("A", "B", "C", "D"):
                self._falla("atenea", "seleccion_unica", f"La pregunta {i} no indica la respuesta correcta (A-D).")
        correctas = [q.get("correcta") for q in su]
        if su and len(set(correctas)) == 1:
            self._falla("atenea", "seleccion_unica", "Todas las respuestas correctas son la misma letra.")

        vf = c["verdadero_falso"].get("afirmaciones", [])
        self._minimo(vf, MINIMOS["verdadero_falso"], "verdadero_falso", "afirmaciones")
        if any(not isinstance(a.get("respuesta"), bool) for a in vf):
            self._falla("atenea", "verdadero_falso", "Hay afirmaciones sin respuesta V o F.")
        if vf and all(a.get("respuesta") for a in vf):
            self._falla("atenea", "verdadero_falso", "Todas son verdaderas: incluye algunas falsas.")

        temas_previos = {h.get("tema", "").lower() for h in exp.historial_previo}
        if exp.encargo.tema and exp.encargo.tema.lower() in temas_previos:
            self._falla("atenea", "tema", f"El tema '{exp.encargo.tema}' ya se trabajó con este curso.")
        else:
            self.ok.append("El tema no repite guías anteriores del archivo.")
        return True

    # ---------------------------------------------------------------- 2. sopa y crucigrama
    def _cuadriculas(self, exp):
        sopa = exp.diseno.get("sopa", {})
        grilla = sopa.get("grilla", [])
        for palabra in exp.contenido["sopa_de_letras"]["palabras"]:
            veces = len(cuadriculas.buscar_en_sopa(grilla, palabra)) if grilla else 0
            if veces == 0:
                self._falla("bauhaus", "sopa_de_letras", f"La palabra {palabra} no está en la sopa.")
            elif veces > 1:
                self._falla("bauhaus", "sopa_de_letras", f"La palabra {palabra} aparece {veces} veces.")
        if not any(o["seccion"] == "sopa_de_letras" for o in self.obs):
            self.ok.append("Sopa de letras: cada palabra aparece exactamente una vez.")

        cruci = exp.diseno.get("crucigrama", {})
        problemas = cuadriculas.verificar_crucigrama(cruci) if cruci else ["No se generó el crucigrama."]
        for p in problemas:
            self._falla("bauhaus", "crucigrama", p)
        if cruci and cruci["ancho"] > 19:
            self._falla("bauhaus", "crucigrama", f"El crucigrama es muy ancho ({cruci['ancho']} columnas).")
        if not problemas:
            self.ok.append(f"Crucigrama: {len(cruci['palabras'])} palabras correctas y con número.")

    # ---------------------------------------------------------------- 3. documento
    def _documento(self, exp):
        arch = exp.archivos
        docx = Path(arch.get("docx", ""))
        if not docx.is_file():
            self._falla("bauhaus", "documento", "No se creó el archivo Word.")
            return
        doc = Document(docx)
        sec = doc.sections[0]
        if abs(sec.page_width - Cm(21.59)) > Cm(0.1) or abs(sec.page_height - Cm(27.94)) > Cm(0.1):
            self._falla("bauhaus", "formato", "La página no es tamaño carta vertical.")
        else:
            self.ok.append("Tamaño carta, orientación vertical.")

        texto = "\n".join(p.text for p in doc.paragraphs).upper()
        texto += "\n".join(c.text for t in doc.tables for f in t.rows for c in f.cells).upper()
        faltan = [s["titulo"] for s in self.formato["secciones"] if s["titulo"].upper() not in texto]
        if faltan:
            self._falla("bauhaus", "formato", f"No aparecen en el Word: {', '.join(faltan)}.")
        else:
            self.ok.append("Todos los títulos de actividad aparecen en el Word.")
        for campo in self.formato["encabezado"]["campos"]:
            if f"{campo.upper()}:" not in texto:
                self._falla("bauhaus", "encabezado", f"Falta el campo '{campo}'.")

        pdf = Path(arch.get("pdf", ""))
        if not pdf.is_file():
            self._falla("bauhaus", "pdf", "No se creó el PDF (¿está instalado LibreOffice?).")
        else:
            from pypdf import PdfReader
            lector = PdfReader(pdf)
            paginas = len(lector.pages)
            for i, pagina in enumerate(lector.pages, start=1):
                lineas = [x for x in (pagina.extract_text() or "").splitlines() if x.strip()]
                # encabezado + pie = 2 líneas; con 1 o 2 más, la página está casi vacía
                if len(lineas) < 5:
                    self._falla("bauhaus", "formato", f"La página {i} quedó casi vacía (contenido cortado).")
            minimo = self.formato["pagina"]["caras_minimas"]
            if paginas < minimo:
                self._falla("atenea", "extension", f"El PDF tiene {paginas} caras; se piden al menos {minimo}.")
            else:
                self.ok.append(f"PDF de {paginas} caras (mínimo {minimo}).")

        for img in exp.diseno.get("imagenes_faltantes", []):
            self.adv.append(f"Falta la imagen {img}: quedó un recuadro para pegarla.")
