"""Herramientas pequeñas para dibujar cosas en Word (líneas, bordes, recuadros).

python-docx no trae algunas funciones (bordes de celdas, números de página),
así que aquí se agregan escribiendo directamente el "código interno" de Word (XML).
"""
from __future__ import annotations

from docx.enum.text import WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


def _elemento(nombre: str, **atributos) -> OxmlElement:
    el = OxmlElement(nombre)
    for k, v in atributos.items():
        el.set(qn(f"w:{k}"), str(v))
    return el


# Orden oficial de los elementos dentro de cada bloque (Word es estricto con esto).
ORDEN = {
    "w:tblPr": ["w:tblStyle", "w:tblpPr", "w:tblOverlap", "w:bidiVisual", "w:tblStyleRowBandSize",
                "w:tblStyleColBandSize", "w:tblW", "w:jc", "w:tblCellSpacing", "w:tblInd",
                "w:tblBorders", "w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook"],
    "w:tcPr": ["w:cnfStyle", "w:tcW", "w:gridSpan", "w:hMerge", "w:vMerge", "w:tcBorders", "w:shd",
               "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign", "w:hideMark"],
    "w:pPr": ["w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr",
              "w:widowControl", "w:numPr", "w:suppressLineNumbers", "w:pBdr", "w:shd", "w:tabs",
              "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap", "w:overflowPunct", "w:topLinePunct",
              "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi", "w:adjustRightInd", "w:snapToGrid",
              "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap",
              "w:jc", "w:textDirection", "w:textAlignment", "w:textboxTightWrap",
              "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange"],
}


def poner(padre, el):
    """Coloca `el` dentro de `padre` en el lugar correcto, reemplazando uno igual si existía."""
    orden = ORDEN[padre.tag.replace(qn("w:x")[:-1], "w:")]
    nombre = el.tag.replace(qn("w:x")[:-1], "w:")
    for viejo in padre.findall(el.tag):
        padre.remove(viejo)
    despues = orden[orden.index(nombre) + 1:]
    for hijo in padre:
        if hijo.tag.replace(qn("w:x")[:-1], "w:") in despues:
            hijo.addprevious(el)
            return el
    padre.append(el)
    return el


def bordes_celda(celda, color="000000", grosor=8, estilo="single", lados=("top", "left", "bottom", "right")):
    tc_pr = celda._tc.get_or_add_tcPr()
    bordes = poner(tc_pr, _elemento("w:tcBorders"))
    for lado in ("top", "left", "bottom", "right"):
        if lado in lados:
            bordes.append(_elemento(f"w:{lado}", val=estilo, sz=grosor, space=0, color=color))
        else:
            bordes.append(_elemento(f"w:{lado}", val="nil"))


def sombrear(celda_o_parrafo, gris="D9D9D9"):
    """Fondo gris (en celdas o párrafos)."""
    if hasattr(celda_o_parrafo, "_tc"):
        props = celda_o_parrafo._tc.get_or_add_tcPr()
    else:
        props = celda_o_parrafo._p.get_or_add_pPr()
    poner(props, _elemento("w:shd", val="clear", color="auto", fill=gris))


def sin_bordes_tabla(tabla):
    tbl_pr = tabla._tbl.tblPr
    bordes = _elemento("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        bordes.append(_elemento(f"w:{lado}", val="nil"))
    poner(tbl_pr, bordes)


def bordes_tabla(tabla, color="000000", grosor=6):
    tbl_pr = tabla._tbl.tblPr
    bordes = _elemento("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        bordes.append(_elemento(f"w:{lado}", val="single", sz=grosor, space=0, color=color))
    poner(tbl_pr, bordes)


def alto_fila(fila, cm: float, exacto=True):
    tr_pr = fila._tr.get_or_add_trPr()
    tr_pr.append(_elemento("w:trHeight", val=int(Cm(cm).twips), hRule="exact" if exacto else "atLeast"))
    no_dividir_fila(fila)


def no_dividir_fila(fila):
    """La fila no se corta entre dos páginas."""
    fila._tr.get_or_add_trPr().append(_elemento("w:cantSplit"))


def ancho_columnas(tabla, anchos_cm: list[float]):
    tabla.autofit = False
    tbl_pr = tabla._tbl.tblPr
    poner(tbl_pr, _elemento("w:tblLayout", type="fixed"))
    poner(tbl_pr, _elemento("w:tblW", w=int(Cm(sum(anchos_cm)).twips), type="dxa"))
    for col, ancho in zip(tabla.columns, anchos_cm):
        col.width = Cm(ancho)
    for fila in tabla.rows:
        for celda, ancho in zip(fila.cells, anchos_cm):
            celda.width = Cm(ancho)


def margenes_celda(celda, cm=0.0):
    tc_pr = celda._tc.get_or_add_tcPr()
    mar = _elemento("w:tcMar")
    for lado in ("top", "left", "bottom", "right"):
        mar.append(_elemento(f"w:{lado}", w=int(Cm(cm).twips), type="dxa"))
    poner(tc_pr, mar)


def linea_para_escribir(contenedor, alto_cm=0.95):
    """Un renglón vacío con una línea gris abajo: para que el estudiante escriba."""
    p = contenedor.add_paragraph()
    fmt = p.paragraph_format
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    fmt.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    fmt.line_spacing = Cm(alto_cm)
    p_pr = p._p.get_or_add_pPr()
    bdr = _elemento("w:pBdr")
    # "between" hace que varias líneas seguidas se vean separadas (si no, Word las junta)
    bdr.append(_elemento("w:bottom", val="single", sz=6, space=1, color="808080"))
    bdr.append(_elemento("w:between", val="single", sz=6, space=1, color="808080"))
    poner(p_pr, bdr)
    return p


def campo(parrafo, instruccion: str):
    """Inserta un campo automático de Word, por ejemplo PAGE o NUMPAGES."""
    run = parrafo.add_run()
    run._r.append(_elemento("w:fldChar", fldCharType="begin"))
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruccion
    run._r.append(instr)
    run._r.append(_elemento("w:fldChar", fldCharType="separate"))
    t = OxmlElement("w:t")
    t.text = "1"
    run._r.append(t)
    run._r.append(_elemento("w:fldChar", fldCharType="end"))
    return run


def no_separar_de_lo_siguiente(parrafo):
    parrafo.paragraph_format.keep_with_next = True
