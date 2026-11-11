"""MEDIDOR DE DIAGRAMACIÓN: abre el PDF y mira cada página como lo haría una persona.

Mide, página por página:
- qué porcentaje está ocupado (para detectar páginas casi vacías);
- si algo se sale de los márgenes (desbordes);
- si hay texto demasiado pequeño;
- el tamaño real de las imágenes;
- si un título de actividad quedó solo al final de una página;
- si la sopa de letras se partió en dos páginas o el crucigrama quedó separado de sus pistas.

Lo usan BAUHAUS (para elegir la mejor distribución) y REVISOR (para controlar).
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

PT_POR_CM = 72 / 2.54
MARGEN_SUP = MARGEN_INF = 1.5 * PT_POR_CM
MARGEN_LAT = 1.8 * PT_POR_CM
ZONA_CABECERA = 38          # pt desde arriba: encabezado repetido
ZONA_PIE = 40               # pt desde abajo: "Página x de y"
FILA_SOPA = re.compile(r"^(?:[A-ZÑ] ){9,}[A-ZÑ]$")
TITULO = re.compile(r"^ACTIVIDAD (\d+)")


def analizar(pdf: Path, letra_minima_pt: float = 10) -> dict:
    paginas = []
    with pdfplumber.open(pdf) as doc:
        for numero, p in enumerate(doc.pages, start=1):
            alto, ancho = p.height, p.width
            util = alto - MARGEN_SUP - MARGEN_INF

            def en_cuerpo(o):
                return o["top"] >= ZONA_CABECERA and o["bottom"] <= alto - ZONA_PIE

            objetos = [o for o in p.chars + p.lines + p.rects + p.images + p.curves if en_cuerpo(o)]
            fondo = max((o["bottom"] for o in objetos), default=MARGEN_SUP)
            ocupacion = max(0.0, min(1.0, (fondo - MARGEN_SUP) / util))

            def fuera(o):
                # Los bordes de tabla sobresalen ~5 pt del margen (normal en Word); el texto y las
                # imágenes no deben salirse.
                tol = 9 if o.get("object_type") in ("line", "rect", "curve") else 4
                return (o["x1"] > ancho - MARGEN_LAT + tol or o["x0"] < MARGEN_LAT - tol
                        or o["bottom"] > alto - MARGEN_INF + tol)

            desbordes = [o for o in objetos if fuera(o)]

            lineas = [ln for ln in p.extract_text_lines() if en_cuerpo(ln)]
            pequenas = []
            bajo_imagen = [(im["bottom"], im["bottom"] + 45) for im in p.images]
            for ln in lineas:
                # créditos de imágenes ("Fuente: ..."): van más pequeños a propósito
                if ln["text"].startswith("Fuente:") or any(a <= ln["top"] <= b for a, b in bajo_imagen):
                    continue
                letras = [c for c in ln["chars"] if c["text"].isalpha()]
                if letras and min(c["size"] for c in letras) < letra_minima_pt - 0.2:
                    pequenas.append((ln["text"][:50], round(min(c["size"] for c in letras), 1)))

            titulos = []
            for ln in lineas:
                m = TITULO.match(ln["text"])
                if m:
                    posicion = (ln["top"] - MARGEN_SUP) / util
                    titulos.append({"numero": int(m.group(1)), "texto": ln["text"], "posicion": round(posicion, 2)})

            imagenes = [{"ancho_cm": round((im["x1"] - im["x0"]) / PT_POR_CM, 1),
                         "alto_cm": round((im["bottom"] - im["top"]) / PT_POR_CM, 1),
                         "arriba": im["top"]} for im in p.images]

            texto = "\n".join(ln["text"] for ln in lineas)
            ultima = next((ln for ln in reversed(lineas)
                           if not re.match(r"^P[áa]gina \d+ de \d+$", ln["text"])), None)
            # recuadros grandes para dibujar (más de 4 cm de alto y casi todo el ancho)
            recuadros = [r for r in p.rects + p.lines
                         if r["bottom"] - r["top"] > 4 * PT_POR_CM and en_cuerpo(r)]
            paginas.append({
                "numero": numero, "ocupacion": round(ocupacion, 2), "desbordes": len(desbordes),
                "letra_pequena": pequenas, "titulos": titulos, "imagenes": imagenes,
                "filas_sopa": sum(1 for ln in lineas if FILA_SOPA.match(ln["text"])),
                # el título puede llevar los minutos al final ("… CRUCIGRAMA ⏱ 9 min")
                "tiene_crucigrama": any("CRUCIGRAMA" in t["texto"] for t in titulos),
                "ultima_linea": ultima["text"] if ultima else "",
                # ¿hay líneas para escribir, recuadros o imágenes debajo de ese último texto?
                "algo_debajo": bool(ultima) and any(o["top"] > ultima["bottom"] + 2
                                                     for o in p.lines + p.rects + p.images if en_cuerpo(o)),
                "tiene_tabla_imagenes": "Ambiente natural" in texto or "Una característica" in texto,
                "tiene_horizontales": "Horizontales" in texto,
                "tiene_verticales": "Verticales" in texto,
                "texto": texto,
                "tiene_recuadro_dibujo": bool(recuadros),
                "tiene_aplicacion": any("APLICACI" in t["texto"] for t in titulos),
            })
    return {"paginas": paginas, "total": len(paginas)}


def problemas(analisis: dict, reglas: dict) -> dict:
    """Clasifica lo encontrado en problemas GRAVES (impiden entregar) y LEVES."""
    graves, leves = [], []
    pags = analisis["paginas"]
    total = analisis["total"]
    ocup_min = reglas.get("ocupacion_minima_pagina", 0.40)
    ocup_ult = reglas.get("ocupacion_minima_ultima", 0.25)
    ancho_min = reglas.get("ancho_minimo_imagen_cm", 6.5)

    for p in pags:
        n = p["numero"]
        es_ultima = n == total
        if p["ocupacion"] < (ocup_ult if es_ultima else ocup_min):
            graves.append(f"La página {n} está casi vacía ({int(p['ocupacion'] * 100)} % ocupado).")
        if p["desbordes"]:
            graves.append(f"En la página {n} hay contenido fuera de los márgenes ({p['desbordes']} elementos).")
        for texto, tam in p["letra_pequena"][:3]:
            graves.append(f"Letra demasiado pequeña ({tam} pt) en la página {n}: «{texto}».")
        for t in p["titulos"]:
            if t["posicion"] > 0.85:
                graves.append(f"El título «{t['texto'][:35]}» quedó solo al final de la página {n}.")
        for im in p["imagenes"]:
            if im["ancho_cm"] < 3.5 and n == 1 and im["arriba"] < 150:
                continue  # es el logo
            if im["ancho_cm"] < ancho_min:
                leves.append(f"Imagen pequeña en la página {n} ({im['ancho_cm']} cm de ancho; mínimo {ancho_min} cm).")

    con_imagenes = [p["numero"] for p in pags
                     if any(not (im["ancho_cm"] < 3.5 and p["numero"] == 1 and im["arriba"] < 150)
                            for im in p["imagenes"])]
    if len(con_imagenes) > 1:
        graves.append(f"Las imágenes de la actividad quedaron repartidas entre las páginas "
                      f"{', '.join(map(str, con_imagenes))}: deben verse juntas.")

    con_sopa = [p["numero"] for p in pags if p["filas_sopa"]]
    if len(con_sopa) > 1:
        graves.append(f"La sopa de letras quedó partida entre las páginas {con_sopa[0]} y {con_sopa[-1]}.")

    pag_cruci = next((p["numero"] for p in pags if p["tiene_crucigrama"]), None)
    if pag_cruci:
        pistas = {p["numero"] for p in pags if p["tiene_horizontales"] or p["tiene_verticales"]}
        if pistas and pag_cruci not in pistas:
            graves.append(f"El crucigrama (página {pag_cruci}) quedó separado de sus pistas (página {min(pistas)}).")
        elif len(pistas) > 1:
            leves.append("Las pistas del crucigrama siguen en la página siguiente.")

    for p in pags[:-1]:
        ultima = p.get("ultima_linea", "").strip()
        if ultima.endswith(":") and not p.get("algo_debajo") and not FILA_SOPA.match(ultima):
            graves.append(f"La página {p['numero']} termina con «{ultima[:45]}», pero lo que anuncia "
                          f"quedó en la página siguiente.")

    pags_img = [p["numero"] for p in pags if p["imagenes"] and not
                all(im["ancho_cm"] < 3.5 and p["numero"] == 1 and im["arriba"] < 150 for im in p["imagenes"])]
    pags_tabla = [p["numero"] for p in pags if p.get("tiene_tabla_imagenes")]
    if pags_img and pags_tabla and pags_tabla[0] not in pags_img:
        leves.append(f"Las imágenes (página {pags_img[0]}) y su tabla para completar "
                     f"(página {pags_tabla[0]}) quedaron en páginas distintas.")

    pag_aplic = next((p["numero"] for p in pags if p["tiene_aplicacion"]), None)
    pags_recuadro = [p["numero"] for p in pags if p["tiene_recuadro_dibujo"]]
    if pag_aplic and pags_recuadro and pag_aplic not in pags_recuadro:
        graves.append(f"Las instrucciones de la aplicación (página {pag_aplic}) quedaron separadas "
                      f"de su recuadro para dibujar (página {pags_recuadro[0]}).")

    numeros = [t["numero"] for p in pags for t in p["titulos"]]
    if numeros != list(range(1, len(numeros) + 1)):
        graves.append(f"Las actividades no aparecen en orden: {numeros}.")
    minimo = reglas.get("paginas_minimas", 4)
    if total < minimo:
        graves.append(f"La guía tiene {total} páginas; el mínimo aprobado (GG-001) es {minimo}.")
    return {"graves": graves, "leves": leves}


def puntaje(analisis: dict, reglas: dict) -> float:
    """Menos es mejor. Sirve para que BAUHAUS compare distribuciones posibles."""
    pr = problemas(analisis, reglas)
    valor = 1000 * len(pr["graves"]) + 50 * len(pr["leves"]) + 4 * analisis["total"]
    for p in analisis["paginas"][:-1]:
        valor += 20 * max(0.0, 0.75 - p["ocupacion"])   # premia páginas bien aprovechadas
    for p in analisis["paginas"]:
        valor -= 3 * sum(1 for t in p["titulos"] if t["posicion"] < 0.2)   # actividades que empiezan arriba
    return round(valor, 2)
