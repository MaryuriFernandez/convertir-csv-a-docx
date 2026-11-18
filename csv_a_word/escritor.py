"""Genera el .docx con el formato del catálogo (Times New Roman 12, A4, títulos centrados)."""

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, Twips

FUENTE = "Times New Roman"
TAMANO = Pt(12)


def _documento() -> Document:
    doc = Document()
    seccion = doc.sections[0]
    # Mismas medidas de página que el catálogo de ejemplo (A4).
    seccion.page_width, seccion.page_height = Twips(11906), Twips(16838)
    seccion.top_margin, seccion.bottom_margin = Twips(1701), Twips(1418)
    seccion.left_margin, seccion.right_margin = Twips(1701), Twips(1418)

    estilo = doc.styles["Normal"]
    estilo.font.name = FUENTE
    estilo.font.size = TAMANO
    estilo.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
    formato = estilo.paragraph_format
    formato.space_before = formato.space_after = Pt(0)
    formato.line_spacing = 1.0
    return doc


def _parrafo(doc, texto="", alineacion=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = alineacion
    if texto:
        p.add_run(texto)
    return p


def escribir_documento(ruta, subseries) -> None:
    """subseries: lista de (lineas_titulo, [descripcion, ...]); descripcion = [(etiqueta, valor), ...]."""
    doc = _documento()
    # Quita el párrafo vacío que python-docx deja al crear el documento.
    cuerpo = doc.element.body
    for p in list(cuerpo.findall(qn("w:p"))):
        cuerpo.remove(p)

    for lineas, descripciones in subseries:
        _parrafo(doc, alineacion=WD_ALIGN_PARAGRAPH.CENTER)
        for linea in lineas:
            _parrafo(doc, linea, WD_ALIGN_PARAGRAPH.CENTER)
        _parrafo(doc)
        for numero, campos in enumerate(descripciones, start=1):
            _parrafo(doc, f"-{numero}-", WD_ALIGN_PARAGRAPH.CENTER)
            for etiqueta, valor in campos:
                _parrafo(doc, f"{etiqueta}: {valor}")
            _parrafo(doc)

    doc.save(ruta)
