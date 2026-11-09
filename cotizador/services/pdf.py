"""
Generación del documento formal de cotización en PDF (tamaño carta).

El PDF es para el cliente: muestra concepto, cantidad, precio unitario y total,
pero NO los costos internos ni los márgenes de ganancia.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (Flowable, Image, KeepTogether, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from ..config import TASA_IVA
from ..formato import fecha_larga, fmt_money, importe_con_letra
from ..models import DocumentoCotizacion, Empresa

# --- Diseño ---
AZUL = colors.HexColor("#1F3A5F")
AZUL_CLARO = colors.HexColor("#E8EEF5")
GRIS = colors.HexColor("#555555")
LINEA = colors.HexColor("#C9D3DF")

MARGEN = 18 * mm
ANCHO_UTIL = letter[0] - 2 * MARGEN
SIN_PADDING_LATERAL = [("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]


def generar_pdf(doc: DocumentoCotizacion, ruta_salida: Path) -> Path:
    """Crea el PDF de la cotización en `ruta_salida` y devuelve esa ruta."""
    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    st = _estilos()

    plantilla = SimpleDocTemplate(
        str(ruta_salida), pagesize=letter,
        leftMargin=MARGEN, rightMargin=MARGEN, topMargin=16 * mm, bottomMargin=18 * mm,
        title=f"Cotización {doc.folio}", author=doc.empresa.nombre,
    )
    contenido: list[Flowable] = [
        _encabezado(doc, st), Spacer(1, 10),
        _bloque_cliente(doc, st), Spacer(1, 12),
        *_introduccion(doc, st), Spacer(1, 10),
        _tabla_conceptos(doc, st), Spacer(1, 6),
        _totales(doc, st), Spacer(1, 16),
        *_condiciones(doc, st), Spacer(1, 30),
        _firma(doc.empresa, st), Spacer(1, 18),
        Paragraph("Gracias por su preferencia.", st["centro"]),
    ]

    def pie(canvas, _plantilla):
        canvas.saveState()
        canvas.setStrokeColor(LINEA)
        canvas.line(MARGEN, 13 * mm, letter[0] - MARGEN, 13 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(GRIS)
        canvas.drawString(MARGEN, 9 * mm, f"{doc.empresa.nombre}  ·  Cotización {doc.folio}")
        canvas.drawRightString(letter[0] - MARGEN, 9 * mm, f"Página {canvas.getPageNumber()}")
        canvas.restoreState()

    plantilla.build(contenido, onFirstPage=pie, onLaterPages=pie)
    return ruta_salida


# ---------------------------------------------------------------------------
# Secciones del documento
# ---------------------------------------------------------------------------

def _encabezado(doc: DocumentoCotizacion, st) -> Table:
    """Datos de la empresa (izquierda) y folio/fechas (derecha)."""
    emp = doc.empresa
    detalles = [d for d in (emp.direccion,
                            f"Tel. {emp.telefono}" if emp.telefono else "",
                            emp.correo,
                            f"RFC: {emp.rfc}" if emp.rfc else "") if d]
    bloque_emp = [Paragraph(_esc(emp.nombre), st["empresa"]), Spacer(1, 2)]
    bloque_emp += [Paragraph(_esc(d), st["gris"]) for d in detalles]

    logo = _logo(emp.logo, 30 * mm, 24 * mm)
    if logo:
        izquierda = Table([[logo, bloque_emp]], colWidths=[33 * mm, None])
        izquierda.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                       ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    else:
        izquierda = bloque_emp

    derecha = Table([
        [Paragraph("COTIZACIÓN", st["titulo"])],
        [Paragraph(f"<b>Folio:</b> {_esc(doc.folio)}", st["der"])],
        [Paragraph(f"<b>Fecha:</b> {fecha_larga(doc.fecha)}", st["der"])],
        [Paragraph(f"<b>Válida hasta:</b> {fecha_larga(doc.fecha_vencimiento)}", st["der"])],
    ], colWidths=[70 * mm])
    derecha.setStyle(TableStyle([
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    tabla = Table([[izquierda, derecha]], colWidths=[ANCHO_UTIL - 72 * mm, 72 * mm])
    tabla.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), *SIN_PADDING_LATERAL,
        ("LINEBELOW", (0, 0), (-1, 0), 2, AZUL), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return tabla


def _bloque_cliente(doc: DocumentoCotizacion, st) -> Table:
    filas = [("Cliente:", doc.cliente.nombre),
             ("Teléfono:", doc.cliente.telefono),
             ("Dirección / obra:", doc.cliente.direccion)]
    datos = [[Paragraph(f"<b>{etq}</b>", st["normal"]), Paragraph(_esc(valor), st["normal"])]
             for etq, valor in filas if valor]
    tabla = Table(datos, colWidths=[32 * mm, ANCHO_UTIL - 32 * mm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL_CLARO),
        ("BOX", (0, 0), (-1, -1), 0.5, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 7), ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
    ]))
    return tabla


def _introduccion(doc: DocumentoCotizacion, st) -> list[Flowable]:
    saludo = f"Estimado(a) {doc.cliente.nombre}:" if doc.cliente.nombre else "Estimado cliente:"
    return [
        Paragraph(_esc(saludo), st["normal"]), Spacer(1, 4),
        Paragraph("Por medio de la presente, nos permitimos poner a su consideración la "
                  "siguiente cotización:", st["normal"]),
    ]


def _tabla_conceptos(doc: DocumentoCotizacion, st) -> Table:
    desc = f"<b>{_esc(doc.descripcion)}</b>"
    if doc.medidas:
        desc += f"<br/>Medidas: {_esc(doc.medidas)}"
    if doc.incluye:
        desc += f'<br/><font color="#555555" size="8.5">Incluye: {_esc(doc.incluye)}</font>'

    anchos = [18 * mm, ANCHO_UTIL - 86 * mm, 34 * mm, 34 * mm]
    tabla = Table([
        [Paragraph(t, st["th"]) for t in ("CANT.", "DESCRIPCIÓN", "PRECIO UNITARIO", "IMPORTE")],
        [Paragraph(str(doc.cantidad), st["centro"]), Paragraph(desc, st["normal"]),
         Paragraph(fmt_money(doc.precio_unitario), st["der"]),
         Paragraph(fmt_money(doc.subtotal), st["der"])],
    ], colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"), ("VALIGN", (0, 1), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINEA),
        ("BOX", (0, 0), (-1, -1), 0.5, LINEA),
    ]))
    return tabla


def _totales(doc: DocumentoCotizacion, st) -> Table:
    """Importe con letra (izquierda) y subtotal/IVA/total (derecha)."""
    filas = [["Subtotal", fmt_money(doc.subtotal)]]
    if doc.incluir_iva:
        filas.append([f"IVA ({TASA_IVA:.0%})", fmt_money(doc.iva)])
    filas.append(["TOTAL", fmt_money(doc.total)])

    totales = Table(filas, colWidths=[34 * mm, 34 * mm])
    totales.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("FONTSIZE", (0, -1), (-1, -1), 11),
        ("BACKGROUND", (0, -1), (-1, -1), AZUL), ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, LINEA),
    ]))
    letra = Paragraph(f"<b>Importe con letra:</b> ({importe_con_letra(doc.total)})", st["letra"])

    fila = Table([[letra, totales]], colWidths=[ANCHO_UTIL - 70 * mm, 70 * mm])
    fila.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), *SIN_PADDING_LATERAL]))
    return fila


def _condiciones(doc: DocumentoCotizacion, st) -> list[Flowable]:
    lineas = [c.strip().replace("{vigencia}", str(doc.vigencia_dias))
              for c in doc.condiciones if c.strip()]
    if not lineas:
        return []
    bloque: list[Flowable] = [Paragraph("Términos y condiciones", st["seccion"]), Spacer(1, 4)]
    bloque += [Paragraph(f"•&nbsp;&nbsp;{_esc(c)}", st["gris"]) for c in lineas]
    return [KeepTogether(bloque)]


def _firma(emp: Empresa, st) -> Flowable:
    filas = [
        [Paragraph("Atentamente", st["centro"])],
        [Spacer(1, 32)],
        [Paragraph(f"<b>{_esc(emp.atiende or emp.nombre)}</b>", st["centro"])],
    ]
    if emp.atiende:
        filas.append([Paragraph(_esc(emp.nombre), st["gris_centro"])])
    tabla = Table(filas, colWidths=[75 * mm])
    tabla.setStyle(TableStyle([("LINEBELOW", (0, 1), (0, 1), 0.8, colors.black)]))
    tabla.hAlign = "CENTER"
    return KeepTogether([tabla])


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _estilos() -> dict[str, ParagraphStyle]:
    base = dict(fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.black)
    gris = {**base, "textColor": GRIS, "fontSize": 8.5, "leading": 11.5}
    return {
        "normal": ParagraphStyle("normal", **base),
        "der": ParagraphStyle("der", **base, alignment=TA_RIGHT),
        "centro": ParagraphStyle("centro", **base, alignment=TA_CENTER),
        "gris": ParagraphStyle("gris", **gris),
        "gris_centro": ParagraphStyle("gris_centro", **gris, alignment=TA_CENTER),
        "letra": ParagraphStyle("letra", **{**base, "fontName": "Helvetica-Oblique",
                                            "fontSize": 8.5}, alignment=TA_LEFT),
        "empresa": ParagraphStyle("empresa", fontName="Helvetica-Bold", fontSize=15,
                                  leading=18, textColor=AZUL),
        "titulo": ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=18,
                                 leading=22, textColor=AZUL, alignment=TA_RIGHT),
        "th": ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9, leading=11,
                             textColor=colors.white, alignment=TA_CENTER),
        "seccion": ParagraphStyle("seccion", fontName="Helvetica-Bold", fontSize=10,
                                  leading=13, textColor=AZUL),
    }


def _esc(texto: str) -> str:
    """Escapa texto del usuario para usarlo dentro de un Paragraph."""
    return (texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("\n", "<br/>"))


def _logo(ruta: str, max_w: float, max_h: float) -> Image | None:
    """Imagen escalada proporcionalmente, o None si no hay un logo válido."""
    if not ruta or not Path(ruta).is_file():
        return None
    try:
        w, h = ImageReader(ruta).getSize()
    except Exception:  # noqa: BLE001 - cualquier imagen ilegible se ignora
        return None
    escala = min(max_w / w, max_h / h)
    return Image(ruta, width=w * escala, height=h * escala)
