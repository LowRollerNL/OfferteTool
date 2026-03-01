import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from models import get_document_lines, get_settings

def draw_logo(canvas, doc, logo_path, width_mm=40, height_mm=20):
    if logo_path and os.path.exists(logo_path):
        width = width_mm * mm
        height = height_mm * mm

        # Rechtsboven positie berekenen
        x = doc.pagesize[0] - width - 20   # 20 = marge
        y = doc.pagesize[1] - height - 20  # 20 = marge

        canvas.drawImage(
            logo_path,
            x,
            y,
            width=width,
            height=height,
            preserveAspectRatio=True,
            mask='auto'
        )

def generate_offerte_pdf(doc, customer, payment_url=None):
    # ===============================
    # Settings ophalen
    # ===============================
    settings = get_settings()
    company_info = {
        "name": settings.get("name", ""),
        "address": settings.get("address", ""),
        "phone": settings.get("phone", ""),
        "email": settings.get("email", ""),
        "iban": settings.get("iban", ""),
        "bic": settings.get("bic", ""),
        "kvk": settings.get("kvk", ""),
        "btw": settings.get("btw", ""),
        "logo_path": settings.get("logo_path", ""),
        "logo_width": 40,
        "logo_height": 20,
        "terms_text": settings.get("terms", "")
    }

    # ===============================
    # PDF bestand pad
    # ===============================
    nummer = doc["number"]
    safe_name = nummer.replace("/", "-").replace(" ", "_")
    pdf_folder = os.path.join(os.getcwd(), "pdf")
    os.makedirs(pdf_folder, exist_ok=True)
    file_path = os.path.join(pdf_folder, f"{safe_name}.pdf")

    pdf = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20
    )

    elements = []

    # ===============================
    # Styles
    # ===============================
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="NormalBold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=styles["Normal"].fontSize, alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name="Wrap", parent=styles["Normal"], wordWrap='CJK', fontSize=10, leading=12))
    styles.add(ParagraphStyle(name="BoldLeft", fontSize=12, leading=14, alignment=TA_LEFT, spaceAfter=4, spaceBefore=10, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="SmallLeft", fontSize=10, leading=12, alignment=TA_LEFT, spaceAfter=2))
    styles.add(ParagraphStyle(name="Terms", fontSize=9, leading=12, alignment=TA_LEFT))

    # ===============================
    # Titel
    # ===============================
    elements.append(Paragraph(f"{doc["type"].capitalize()} {nummer}", styles["Heading1"]))
    elements.append(Spacer(1, 10))


    # -------------------------------
    # 2. Klant en bedrijfsgegevens
    # -------------------------------
    customer_paragraph = Paragraph(
        f"<b>Aan:</b><br/>"
        f"<b>Klant:</b> {customer[1]}<br/>"
        f"<b>Adres:</b> {customer[4] or ''}<br/>"
        f"<b>Email:</b> {customer[2] or ''}<br/>"
        f"<b>Telefoon:</b> {customer[3] or ''}",
        styles["Normal"]
    )

    company_paragraph = Paragraph(
        f"<b>{company_info['name']}</b><br/>"
        f"{company_info['address']}<br/>"
        f"Tel: {company_info['phone']}<br/>"
        f"Email: {company_info['email']}<br/>"
        f"IBAN: {company_info['iban']} | BIC: {company_info['bic']}<br/>"
        f"KvK: {company_info['kvk']} | BTW: {company_info['btw']}",
        styles["Normal"]
    )

    info_table = Table(
        [[customer_paragraph, company_paragraph]],
        colWidths=[300, 250]
    )

    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # ===============================
    # Documentregels
    # ===============================
    lines = get_document_lines(doc["id"])
    data = [["Omschrijving", "Aantal", "Prijs", "BTW %", "Totaal"]]
    for line in lines:
        data.append([
            Paragraph(line[2], styles["Wrap"]),
            line[3],
            f"€ {line[5]:.2f}",
            f"{line[7]}%",
            f"€ {line[8]:.2f}"
        ])

    table_lines = Table(data, colWidths=[220, 50, 80, 50, 80])
    table_lines.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
    ]))
    elements.append(table_lines)
    elements.append(Spacer(1, 20))

    # ===============================
    # Totaalregels
    # ===============================
    elements.append(Paragraph(f"Totaal excl. BTW: € {doc["total_excl"]:.2f}", styles["NormalBold"]))
    elements.append(Paragraph(f"BTW: € {doc["total_btw"]:.2f}", styles["NormalBold"]))
    elements.append(Paragraph(f"Totaal incl. BTW: € {doc["total_incl"]:.2f}", styles["NormalBold"]))

    # ===============================
    # Voorwaarden
    # ===============================
    terms_text = company_info.get("terms_text", "")
    if terms_text:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Voorwaarden:", styles["BoldLeft"]))
        elements.append(Paragraph(company_info["terms_text"], styles["Terms"]))

    # ===============================
    # Handtekening / akkoord sectie
    # ===============================
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Voor akkoord:", styles["BoldLeft"]))
    elements.append(Paragraph("Naam / Handtekening", styles["SmallLeft"]))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("______________________________", styles["SmallLeft"]))

    # ===============================
    # PDF bouwen
    # ===============================
    pdf.build(
    elements,
    onFirstPage=lambda canvas, doc: draw_logo(
        canvas,
        doc,
        company_info["logo_path"],
        company_info["logo_width"],
        company_info["logo_height"]
    )
)
    return file_path