from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

OUTPUT = "/home/user/claude_testing/gastos-tracker-cl.pdf"

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=2.5*cm, rightMargin=2.5*cm,
    topMargin=2.5*cm, bottomMargin=2.5*cm
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle("title", parent=styles["Title"],
    fontSize=22, textColor=colors.HexColor("#1a1a2e"), spaceAfter=6, alignment=TA_CENTER)

subtitle_style = ParagraphStyle("subtitle", parent=styles["Normal"],
    fontSize=11, textColor=colors.HexColor("#4a4a6a"), spaceAfter=20, alignment=TA_CENTER)

h2_style = ParagraphStyle("h2", parent=styles["Heading2"],
    fontSize=13, textColor=colors.HexColor("#1a1a2e"), spaceBefore=18, spaceAfter=6,
    borderPad=4)

body_style = ParagraphStyle("body", parent=styles["Normal"],
    fontSize=10, textColor=colors.HexColor("#333333"), leading=16, spaceAfter=6)

bullet_style = ParagraphStyle("bullet", parent=body_style,
    leftIndent=16, bulletIndent=6, spaceAfter=4)

note_style = ParagraphStyle("note", parent=body_style,
    fontSize=9, textColor=colors.HexColor("#666666"), leftIndent=12, spaceAfter=4)

story = []

# --- HEADER ---
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("gastos-tracker-cl", title_style))
story.append(Paragraph("Rastreador de gastos personales · Banca chilena", subtitle_style))
story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4a90d9")))
story.append(Spacer(1, 0.4*cm))

# --- QUÉ ES ---
story.append(Paragraph("¿Qué es?", h2_style))
story.append(Paragraph(
    "Una API REST desarrollada en Python que permite llevar un control detallado de los gastos personales "
    "a partir de las cartolas bancarias de <b>Santander</b> y <b>Falabella</b> en Chile. "
    "El objetivo es tener toda la información financiera consolidada en un solo lugar, "
    "con categorización automática, presupuestos y reportes.",
    body_style))

# --- PROBLEMA QUE RESUELVE ---
story.append(Paragraph("Problema que resuelve", h2_style))
items = [
    "Las cartolas bancarias son difíciles de analizar directamente desde el banco.",
    "No hay una vista unificada cuando se tienen cuentas en múltiples bancos.",
    "Categorizar gastos manualmente es tedioso y propenso a errores.",
    "No existe una forma sencilla de definir presupuestos y recibir alertas.",
]
for item in items:
    story.append(Paragraph(f"• {item}", bullet_style))

# --- FUNCIONALIDADES ---
story.append(Paragraph("Funcionalidades principales", h2_style))

features = [
    ["Módulo", "Descripción"],
    ["Importación de cartolas", "Lee archivos Excel/CSV de Santander y Falabella y guarda las transacciones automáticamente."],
    ["Gestión de transacciones", "CRUD completo: crear, consultar, editar y eliminar transacciones."],
    ["Categorización automática", "Detecta la categoría del gasto por la descripción (supermercado, transporte, etc.)."],
    ["Presupuestos", "Define límites de gasto por categoría y recibe alertas al acercarte al límite."],
    ["Reportes", "Resúmenes de gasto por período y categoría, exportables a CSV."],
    ["Scrapers web", "Módulos alternativos para obtener transacciones directamente desde la web del banco."],
]

table = Table(features, colWidths=[4.5*cm, 12*cm])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 10),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f5f7ff"), colors.white]),
    ("FONTSIZE", (0, 1), (-1, -1), 9),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ("ROUNDEDCORNERS", [4]),
]))
story.append(table)

# --- STACK TÉCNICO ---
story.append(Paragraph("Stack técnico", h2_style))
tech = [
    ("Lenguaje", "Python 3"),
    ("Framework API", "FastAPI"),
    ("Base de datos", "SQLite (SQLAlchemy ORM)"),
    ("Parseo de cartolas", "Pandas (Excel/CSV)"),
    ("Scraping web", "Selenium + BeautifulSoup"),
    ("Tests", "Pytest con fixtures y casos de borde"),
    ("Formato de entrega", "API REST con JSON"),
]
for k, v in tech:
    story.append(Paragraph(f"<b>{k}:</b> {v}", bullet_style))

# --- ESTRUCTURA ---
story.append(Paragraph("Estructura del proyecto", h2_style))
story.append(Paragraph(
    "El código está organizado en módulos independientes dentro de <code>gastos_tracker/app/</code>:",
    body_style))

estructura = [
    "importers/ — Parseo de cartolas Santander y Falabella",
    "scrapers/  — Obtención de datos vía web scraping",
    "routers/   — Endpoints de la API (transacciones, presupuestos, reportes, etc.)",
    "services/  — Lógica de negocio: categorización, alertas, exportación",
    "models.py  — Modelos de base de datos",
    "schemas.py — Validación de datos de entrada/salida",
    "tests/     — Suite completa de pruebas automatizadas",
]
for line in estructura:
    story.append(Paragraph(f"<font name='Courier' size='9'>{line}</font>", bullet_style))

# --- ESTADO ---
story.append(Paragraph("Estado actual", h2_style))
story.append(Paragraph(
    "El proyecto está en fase de desarrollo activo. La funcionalidad principal está implementada "
    "y probada. Se encuentra en una rama de feature lista para integrarse a la rama principal (<code>main</code>).",
    body_style))

story.append(Spacer(1, 0.3*cm))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    "Repositorio: github.com/migueljimenop/gastos-tracker-cl  ·  Marzo 2026",
    note_style))

doc.build(story)
print(f"PDF generado: {OUTPUT}")
