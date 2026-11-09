"""REVISOR — CALIDAD.

Recibe: exp.contenido + exp.diseno + exp.archivos + exp.lecciones.
Entrega: exp.revision = {
    "aprobada": True/False,
    "observaciones": [{"responsable": "atenea"|"bauhaus"|"profesor", "seccion", "problema"}],
    "advertencias": [...],      # conviene mirarlas, pero no impiden entregar
    "comprobaciones": [...],    # lo que se revisó y estaba bien
}

REVISOR no confía en los demás: vuelve a buscar cada palabra en la sopa,
lee el crucigrama letra por letra, abre el PDF y mira página por página.

Grupos de controles:
  1. Contenido completo           4. Imágenes y logo
  2. Claridad y dificultad        5. Diagramación (Word y PDF)
  3. Sopa de letras y crucigrama  6. Objetivos de aprendizaje y lecciones aprobadas
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.shared import Cm

from .. import configuracion, cuadriculas, memoria
from .. import legibilidad as leg
from ..curriculo import niveles_de
from ..expediente import Expediente
from .base import Agente

MINIMOS = {"sopa_palabras": 8, "crucigrama_pistas": 6, "lectura_parrafos": 3,
           "lectura_preguntas": 3, "seleccion_unica": 4, "verdadero_falso": 4}

VERBOS_INSTRUCCION = (
    "lee", "escribe", "encierra", "marca", "completa", "observa", "responde", "dibuja", "elige",
    "encuentra", "busca", "compara", "explica", "nombra", "une", "ordena", "pinta", "subraya",
    "imagina", "piensa", "describe", "identifica", "clasifica", "corrige", "comenta", "crea",
    "diseña", "investiga", "anota", "indica", "relaciona", "recorta", "pega", "comparte", "dialoga",
)
ABSOLUTOS = ("siempre", "nunca", "todos", "todas", "ninguno", "ninguna", "jamás", "solo", "sólo")
SECCIONES_CON_INSTRUCCION = ("actividad_inicial", "sopa_de_letras", "crucigrama", "analisis_imagenes",
                             "seleccion_unica", "verdadero_falso", "aplicacion")


class Revisor(Agente):
    nombre = "revisor"

    def __init__(self):
        self.formato = configuracion.leer("formato_guia")
        self.niveles = configuracion.leer("niveles")

    # ================================================================ principal
    def trabajar(self, exp: Expediente) -> Expediente:
        self.obs, self.adv, self.ok = [], [], []
        self.exigencias = self._exigencias(exp)
        c = exp.contenido
        if self._contenido(exp, c):
            self._claridad(c)
            self._cuadriculas(exp)
            self._imagenes(exp)
        self._oa(c)
        self._documento(exp)

        exp.revision = {"aprobada": not self.obs, "observaciones": self.obs,
                        "advertencias": self.adv, "comprobaciones": self.ok}
        for o in self.obs:
            exp.anotar("revisor", o["responsable"], "solicitud_correccion",
                       f"[{o['seccion']}] {o['problema']}")
        if not self.obs:
            exp.anotar("revisor", "archivo", "entrega",
                       f"Guía aprobada ({len(self.adv)} advertencia(s) para el profesor).")
        return exp

    # ================================================================ ayudas
    def _falla(self, quien, seccion, problema):
        self.obs.append({"responsable": quien, "seccion": seccion, "problema": problema})

    def _ojo(self, seccion, texto):
        self.adv.append(f"[{seccion}] {texto}")

    def _minimo(self, lista, minimo, seccion, que):
        if len(lista) < minimo:
            self._falla("atenea", seccion, f"Tiene {len(lista)} {que}; se necesitan al menos {minimo}.")
        else:
            self.ok.append(f"{seccion}: {len(lista)} {que}.")

    def _exigencias(self, exp) -> dict:
        """Exigencias del nivel más alto del curso + reglas aprobadas por el profesor."""
        niveles = niveles_de(exp.encargo.cursos)
        elegido = None
        for grupo in self.niveles.values():
            if set(grupo["niveles"]) & set(niveles):
                elegido = grupo   # si hay 5.º y 6.º, ambos son del mismo grupo; 7.º-8.º manda si aparece
        exigencias = dict(elegido or self.niveles["basica_5_6"])
        reglas = memoria.reglas(exp.lecciones)
        exigencias.update({k: v for k, v in reglas.items() if k in exigencias})
        exigencias["palabras_prohibidas"] = reglas.get("palabras_prohibidas", [])
        return exigencias

    @staticmethod
    def _textos(c) -> list[tuple[str, str]]:
        """Todos los textos que leerá el estudiante, con la sección donde están."""
        t = []
        for sec in SECCIONES_CON_INSTRUCCION:
            if c.get(sec, {}).get("instruccion"):
                t.append((sec, c[sec]["instruccion"]))
        for sec in ("actividad_inicial", "lectura", "analisis_imagenes", "ticket_salida"):
            t += [(sec, q["texto"]) for q in c.get(sec, {}).get("preguntas", [])]
        t += [("lectura", x) for x in c.get("lectura", {}).get("parrafos", [])]
        t += [("seleccion_unica", q["texto"]) for q in c.get("seleccion_unica", {}).get("preguntas", [])]
        t += [("seleccion_unica", a) for q in c.get("seleccion_unica", {}).get("preguntas", [])
              for a in q.get("alternativas", [])]
        t += [("verdadero_falso", a["texto"]) for a in c.get("verdadero_falso", {}).get("afirmaciones", [])]
        t += [("crucigrama", p["pista"]) for p in c.get("crucigrama", {}).get("pistas", [])]
        t += [("aplicacion", p) for p in c.get("aplicacion", {}).get("pasos", [])]
        return t

    # ================================================================ 1. contenido
    def _contenido(self, exp, c) -> bool:
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
        if vf and not any(a.get("respuesta") for a in vf):
            self._falla("atenea", "verdadero_falso", "Todas son falsas: incluye algunas verdaderas.")
        for i, a in enumerate(vf, 1):
            if a.get("respuesta") is False and not a.get("correccion"):
                self._ojo("verdadero_falso", f"La afirmación {i} es falsa pero no trae su corrección para el solucionario.")

        temas_previos = {h.get("tema", "").lower() for h in exp.historial_previo}
        if exp.encargo.tema and exp.encargo.tema.lower() in temas_previos:
            self._falla("atenea", "tema", f"El tema '{exp.encargo.tema}' ya se trabajó con este curso.")
        else:
            self.ok.append("El tema no repite guías anteriores del archivo.")

        prohibidas = self.exigencias["palabras_prohibidas"]
        if prohibidas:
            for sec, texto in self._textos(c):
                for palabra in prohibidas:
                    if re.search(rf"\b{re.escape(leg.sin_tildes(palabra))}\b", leg.sin_tildes(texto)):
                        self._falla("atenea", sec, f"Usa la palabra '{palabra}', prohibida por una lección aprobada.")
        return not any(o["responsable"] == "atenea" and o["seccion"] in ("sopa_de_letras", "crucigrama")
                       for o in self.obs)

    # ================================================================ 2. claridad y dificultad
    def _claridad(self, c):
        ex = self.exigencias
        antes = len(self.obs) + len(self.adv)

        # Instrucciones: deben existir, decir QUÉ hacer (verbo) y no ser muy largas
        for sec in SECCIONES_CON_INSTRUCCION:
            instr = c[sec].get("instruccion", "").strip()
            if not instr:
                self._falla("atenea", sec, "Falta la instrucción: el estudiante no sabrá qué hacer.")
                continue
            palabras = leg.sin_tildes(instr).split()
            if not any(re.sub(r"\W", "", p) in {leg.sin_tildes(v) for v in VERBOS_INSTRUCCION} for p in palabras):
                self._ojo(sec, "La instrucción no tiene un verbo de acción claro (lee, escribe, encierra...).")
            if len(palabras) > ex["max_palabras_instruccion"]:
                self._ojo(sec, f"Instrucción larga ({len(palabras)} palabras; máximo sugerido {ex['max_palabras_instruccion']}).")

        # Preguntas: no vacías, no dobles, no demasiado largas
        for sec in ("actividad_inicial", "lectura", "ticket_salida"):
            for i, q in enumerate(c[sec].get("preguntas", []), 1):
                texto = q.get("texto", "").strip()
                if not texto:
                    self._falla("atenea", sec, f"La pregunta {i} está vacía.")
                    continue
                if texto.count("?") > 2:
                    self._ojo(sec, f"La pregunta {i} tiene varias preguntas juntas; puede confundir.")
                if leg.contar_palabras(texto) > ex["max_palabras_pregunta"]:
                    self._ojo(sec, f"La pregunta {i} es larga ({leg.contar_palabras(texto)} palabras).")

        # Lectura: extensión, legibilidad, oraciones largas, vocabulario difícil
        texto = " ".join(c["lectura"].get("parrafos", []))
        n = leg.contar_palabras(texto)
        if n < ex["lectura_min_palabras"]:
            self._ojo("lectura", f"Lectura corta ({n} palabras); quizás no alcance para 90 minutos.")
        elif n > ex["lectura_max_palabras"]:
            self._falla("atenea", "lectura", f"Lectura demasiado larga para el nivel ({n} palabras; máximo {ex['lectura_max_palabras']}).")
        indice = leg.indice_inflesz(texto)
        if indice < ex["legibilidad_minima"] - 10:
            self._falla("atenea", "lectura", f"Lectura muy difícil para el nivel (índice {indice}: {leg.escala(indice)}).")
        elif indice < ex["legibilidad_minima"]:
            self._ojo("lectura", f"Lectura algo difícil para el nivel (índice {indice}: {leg.escala(indice)}; sugerido ≥ {ex['legibilidad_minima']}).")
        else:
            self.ok.append(f"Lectura de {n} palabras, legibilidad {indice} ({leg.escala(indice)}).")
        for o in leg.oraciones_largas(texto, ex["max_palabras_oracion"]):
            self._ojo("lectura", f"Oración larga ({leg.contar_palabras(o)} palabras): «{o[:70]}…»")
        dificiles = leg.palabras_dificiles(texto)
        if n and len(dificiles) / n > ex["max_palabras_dificiles"]:
            self._ojo("lectura", f"Muchas palabras largas o difíciles: {', '.join(dificiles[:8])}.")

        # Selección única: alternativas distintas, sin pistas involuntarias
        su = c["seleccion_unica"]["preguntas"]
        for i, q in enumerate(su, 1):
            alts = [a.strip().lower() for a in q.get("alternativas", [])]
            if len(set(alts)) != len(alts):
                self._falla("atenea", "seleccion_unica", f"La pregunta {i} tiene alternativas repetidas.")
            if any("todas las anteriores" in a or "ninguna de las anteriores" in a for a in alts):
                self._ojo("seleccion_unica", f"La pregunta {i} usa 'todas/ninguna de las anteriores'; es menos clara.")
            if re.search(r"\bno\b", q.get("texto", "")) and "NO" not in q.get("texto", ""):
                self._ojo("seleccion_unica", f"La pregunta {i} es negativa: escribe el NO en mayúsculas para destacarlo.")
            if q.get("correcta") in "ABCD" and len(alts) == 4:
                largo_ok = len(alts["ABCD".index(q["correcta"])])
                otros = [len(a) for j, a in enumerate(alts) if j != "ABCD".index(q["correcta"])]
                if otros and largo_ok > 1.8 * (sum(otros) / len(otros)) and largo_ok - max(otros) > 15:
                    self._ojo("seleccion_unica", f"En la pregunta {i} la correcta es mucho más larga que las otras (se adivina).")
        letras = [q.get("correcta") for q in su]
        for letra in set(letras):
            if letras.count(letra) > len(letras) / 2 and len(letras) >= 4:
                self._ojo("seleccion_unica", f"La letra {letra} es la correcta en más de la mitad de las preguntas.")

        # Verdadero o falso: proporción y palabras absolutas
        vf = c["verdadero_falso"]["afirmaciones"]
        verdaderas = sum(1 for a in vf if a.get("respuesta"))
        if vf and not 0.3 <= verdaderas / len(vf) <= 0.7:
            self._ojo("verdadero_falso", f"Hay {verdaderas} verdaderas de {len(vf)}; conviene equilibrar.")
        for i, a in enumerate(vf, 1):
            if any(re.search(rf"\b{w}\b", a["texto"].lower()) for w in ABSOLUTOS):
                self._ojo("verdadero_falso", f"La afirmación {i} usa palabras absolutas (siempre, nunca, todos...): delatan la respuesta.")

        # Palabras de sopa y crucigrama: sin repetidas, largo razonable, respuesta no escrita en la pista
        for sec, lista in (("sopa_de_letras", c["sopa_de_letras"]["palabras"]),
                           ("crucigrama", [p["palabra"] for p in c["crucigrama"]["pistas"]])):
            normales = [cuadriculas.normalizar(p) for p in lista]
            repetidas = {p for p in normales if normales.count(p) > 1}
            if repetidas:
                self._falla("atenea", sec, f"Palabras repetidas: {', '.join(sorted(repetidas))}.")
            cortas = [p for p in normales if len(p) < 3]
            if cortas:
                self._ojo(sec, f"Palabras muy cortas: {', '.join(cortas)}.")
            largas = [p for p in normales if len(p) > 13]
            if largas:
                self._falla("atenea", sec, f"Palabras demasiado largas para la cuadrícula: {', '.join(largas)}.")
        for p in c["crucigrama"]["pistas"]:
            if leg.sin_tildes(p["palabra"]) in leg.sin_tildes(p["pista"]):
                self._falla("atenea", "crucigrama", f"La pista de {p['palabra'].upper()} contiene la respuesta.")
            if leg.contar_palabras(p["pista"]) < 3:
                self._ojo("crucigrama", f"La pista de {p['palabra'].upper()} es muy breve; puede ser ambigua.")

        # Palabras de la sopa que no aparecen en ninguna parte de la guía (sin contexto)
        todo = leg.sin_tildes(" ".join(t for _, t in self._textos(c)))
        sueltas = [p for p in c["sopa_de_letras"]["palabras"] if leg.sin_tildes(p) not in todo]
        if len(sueltas) > len(c["sopa_de_letras"]["palabras"]) / 2:
            self._ojo("sopa_de_letras", f"Varias palabras no se trabajan en la guía: {', '.join(sueltas)}.")

        if len(self.obs) + len(self.adv) == antes:
            self.ok.append("Claridad: instrucciones, preguntas y alternativas sin problemas.")

    # ================================================================ 3. cuadrículas
    def _cuadriculas(self, exp):
        sopa = exp.diseno.get("sopa", {})
        grilla = sopa.get("grilla", [])
        if grilla and any(len(f) != len(grilla) for f in grilla):
            self._falla("bauhaus", "sopa_de_letras", "La sopa no es cuadrada.")
        if grilla and any(not letra or letra not in cuadriculas.ALFABETO for f in grilla for letra in f):
            self._falla("bauhaus", "sopa_de_letras", "La sopa tiene casillas vacías o símbolos raros.")
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
        if cruci:
            inicios = [(p["numero"], p["direccion"]) for p in cruci["palabras"]]
            if len(set(inicios)) != len(inicios):
                problemas.append("Hay dos palabras con el mismo número y dirección.")
            pistas = {cuadriculas.normalizar(p["palabra"]) for p in exp.contenido["crucigrama"]["pistas"]}
            if {p["palabra"] for p in cruci["palabras"]} | {p["palabra"] for p in cruci["no_ubicadas"]} != pistas:
                problemas.append("Las palabras del crucigrama no coinciden con las pistas.")
            if cruci["ancho"] > 19 or cruci["alto"] > 20:
                problemas.append(f"El crucigrama es muy grande ({cruci['ancho']}x{cruci['alto']}).")
            if not self._conectado(cruci):
                problemas.append("Hay palabras del crucigrama que no se cruzan con las demás.")
        for p in problemas:
            self._falla("bauhaus", "crucigrama", p)
        if not problemas:
            self.ok.append(f"Crucigrama: {len(cruci['palabras'])} palabras correctas, conectadas y numeradas.")

    @staticmethod
    def _conectado(cruci) -> bool:
        celdas = {(f, c) for f, fila in enumerate(cruci["grilla"]) for c, x in enumerate(fila) if x}
        if not celdas:
            return False
        pendientes, vistas = [next(iter(celdas))], set()
        while pendientes:
            f, c = pendientes.pop()
            if (f, c) in vistas:
                continue
            vistas.add((f, c))
            pendientes += [v for v in ((f + 1, c), (f - 1, c), (f, c + 1), (f, c - 1)) if v in celdas]
        return vistas == celdas

    # ================================================================ 4. imágenes y logo
    def _imagenes(self, exp):
        imagenes = exp.diseno.get("imagenes", [])
        for img in imagenes:
            if img["estado"] == "falta":
                self._falla("profesor", "imagenes",
                            f"Falta la imagen '{img['id']}' ({img['descripcion'] or img['pie']}). "
                            f"Ver recursos/entrada/PEDIDO_DE_IMAGENES.md.")
                continue
            if img["estado"] == "provisoria":
                self._ojo("imagenes", f"'{img['id']}' es un dibujo provisorio hecho por código; conviene una foto o ilustración real.")
            elif not img.get("fuente"):
                self._ojo("imagenes", f"'{img['id']}' no tiene anotada su fuente/licencia.")
            for problema in (img.get("calidad") or {}).get("problemas", []):
                self._ojo("imagenes", f"'{img['id']}': {problema}.")
        if imagenes and not any(i["estado"] == "falta" for i in imagenes):
            self.ok.append(f"Las {len(imagenes)} imágenes están disponibles.")
        if exp.diseno.get("logo"):
            self.ok.append("Logo institucional incluido.")
        else:
            self._ojo("logo", "No hay logo guardado: se imprime un recuadro 'LOGO'. Usa: python recursos.py logo <archivo>")

    # ================================================================ 6. OA
    def _oa(self, c):
        for oa in c.get("oa_verificacion", []):
            if oa["estado"] == "verificado":
                self.ok.append(f"{oa['codigo']} verificado con fuente oficial ({oa['fuente']}).")
            elif oa["estado"] == "pendiente":
                self._ojo("oa", f"Objetivo de aprendizaje {oa['codigo'] or ''} PENDIENTE DE CONFIRMACIÓN: {oa['motivo']}")

    # ================================================================ 5. diagramación
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
        if "[FALTA IMAGEN" in texto:
            self._ojo("imagenes", "El Word tiene recuadros de imágenes faltantes.")

        pdf = Path(arch.get("pdf", ""))
        if not pdf.is_file():
            self._falla("bauhaus", "pdf", "No se creó el PDF (¿está instalado LibreOffice?).")
            return
        from pypdf import PdfReader
        lector = PdfReader(pdf)
        paginas = len(lector.pages)
        antes = len(self.obs)
        textos = [(pagina.extract_text() or "") for pagina in lector.pages]
        for i, t in enumerate(textos, start=1):
            lineas = [x.strip() for x in t.splitlines() if x.strip()]
            utiles = [x for x in lineas if not re.match(r"^P[áa]gina \d+ de \d+$", x)
                      and not x.startswith(self._cabecera(exp))]
            if len(lineas) < 5:
                self._falla("bauhaus", "diagramacion", f"La página {i} quedó casi vacía (contenido cortado).")
            if utiles and re.match(r"^ACTIVIDAD \d+", utiles[-1]):
                self._falla("bauhaus", "diagramacion", f"La página {i} termina con un título suelto ({utiles[-1][:30]}).")
        numeros = [int(n) for n in re.findall(r"ACTIVIDAD (\d+)", "\n".join(textos))]
        if numeros != list(range(1, len(numeros) + 1)):
            self._falla("bauhaus", "diagramacion", f"Las actividades no aparecen en orden en el PDF: {numeros}.")
        esperadas = sum(1 for i in exp.diseno.get("imagenes", []) if i["ruta"]) + (1 if exp.diseno.get("logo") else 0)
        en_pdf = sum(len(p.images) for p in lector.pages)
        if en_pdf < esperadas:
            self._falla("bauhaus", "imagenes", f"El PDF muestra {en_pdf} imágenes y se esperaban {esperadas}.")
        if len(self.obs) == antes:
            self.ok.append("Diagramación: sin páginas vacías, títulos sueltos ni imágenes perdidas.")

        minimo = self.formato["pagina"]["caras_minimas"]
        maximo = self.exigencias.get("paginas_maximas", 99)
        if paginas < minimo:
            self._falla("atenea", "extension", f"El PDF tiene {paginas} caras; se piden al menos {minimo}.")
        else:
            self.ok.append(f"PDF de {paginas} caras (mínimo {minimo}).")
        if paginas > maximo:
            self._ojo("extension", f"La guía tiene {paginas} caras (más de {maximo}); gasta más papel.")

    @staticmethod
    def _cabecera(exp) -> str:
        return configuracion.leer("escuela")["escuela"]["nombre"]
