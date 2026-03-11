"""PDF generator for Mekano devis using ReportLab."""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

# Mekano brand colors
MEKANO_BLUE = colors.HexColor("#3176A6")
MEKANO_DARK = colors.HexColor("#1a2332")
LIGHT_GRAY = colors.HexColor("#f5f5f5")
MID_GRAY = colors.HexColor("#dddddd")
TEXT_GRAY = colors.HexColor("#555555")


def _fmt_chf(val):
    if val is None:
        return "-"
    return f"CHF {float(val):,.2f}".replace(",", "'")


def _fmt_date(dt):
    if not dt:
        return "-"
    if hasattr(dt, 'strftime'):
        return dt.strftime("%d.%m.%Y")
    return str(dt)[:10]


def generate_devis_pdf(devis, garage):
    """Generate a professional PDF for a devis. Returns bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontName = "Helvetica"
    normal.fontSize = 9

    def style(name, **kw):
        s = ParagraphStyle(name, parent=normal, **kw)
        return s

    title_style = style("title", fontSize=18, textColor=MEKANO_BLUE, fontName="Helvetica-Bold")
    h2_style = style("h2", fontSize=10, textColor=MEKANO_DARK, fontName="Helvetica-Bold")
    small_gray = style("small_gray", fontSize=8, textColor=TEXT_GRAY)
    right_style = style("right", alignment=TA_RIGHT)
    bold_style = style("bold", fontName="Helvetica-Bold", fontSize=9)
    total_style = style("total", fontName="Helvetica-Bold", fontSize=11, textColor=MEKANO_BLUE)

    story = []
    W = A4[0] - 30*mm  # usable width

    # ── HEADER ──────────────────────────────────────────────
    header_data = [
        [
            Paragraph(f"<font color='#{MEKANO_BLUE.hexval()[2:]}' size='16'><b>Me</b></font>"
                      f"<font color='#{MEKANO_BLUE.hexval()[2:]}' size='16'><b>kano</b></font>", title_style),
            Paragraph(
                f"<b>{garage.nom}</b><br/>"
                f"{garage.adresse or ''}<br/>"
                f"{garage.npa or ''} {garage.localite or ''}<br/>"
                f"Tél: {garage.telephone or ''}<br/>"
                f"{garage.email or ''}",
                style("garage_info", fontSize=8, textColor=TEXT_GRAY, alignment=TA_RIGHT)
            )
        ]
    ]
    header_table = Table(header_data, colWidths=[W*0.5, W*0.5])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=MEKANO_BLUE, spaceAfter=6))

    # ── DEVIS TITLE + META ───────────────────────────────────
    meta_data = [
        [
            Paragraph(f"DEVIS N° <b>{devis.numero}</b>", style("dev_title", fontSize=14, fontName="Helvetica-Bold", textColor=MEKANO_DARK)),
            Table([
                [Paragraph("Date :", small_gray), Paragraph(_fmt_date(devis.date_creation), bold_style)],
                [Paragraph("Valable jusqu'au :", small_gray), Paragraph(_fmt_date(devis.date_validite), bold_style)],
                [Paragraph("Statut :", small_gray), Paragraph(devis.statut.upper(), bold_style)],
            ], colWidths=[35*mm, 40*mm], style=TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
        ]
    ]
    meta_table = Table(meta_data, colWidths=[W*0.55, W*0.45])
    meta_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(Spacer(1, 4*mm))
    story.append(meta_table)
    story.append(Spacer(1, 4*mm))

    # ── CLIENT + VEHICULE ────────────────────────────────────
    client = devis.client
    vehicule = devis.vehicule
    cv_data = [
        [
            [
                Paragraph("CLIENT", style("section_label", fontSize=7, textColor=MEKANO_BLUE, fontName="Helvetica-Bold")),
                Paragraph(f"<b>{client.prenom} {client.nom}</b>" if client else "-", bold_style),
                Paragraph(f"{client.adresse or ''}" if client else "", small_gray),
                Paragraph(f"{client.npa or ''} {client.localite or ''}" if client else "", small_gray),
                Paragraph(f"Tél: {client.telephone or '-'}" if client else "", small_gray),
                Paragraph(f"{client.email or ''}" if client else "", small_gray),
            ],
            [
                Paragraph("VÉHICULE", style("section_label2", fontSize=7, textColor=MEKANO_BLUE, fontName="Helvetica-Bold")),
                Paragraph(
                    f"<b>{vehicule.marque} {vehicule.modele}</b>" if vehicule else "-",
                    bold_style
                ),
                Paragraph(f"Plaque : {vehicule.plaque or '-'}" if vehicule else "", small_gray),
                Paragraph(f"Année : {vehicule.annee or '-'}" if vehicule else "", small_gray),
                Paragraph(f"VIN : {vehicule.vin or '-'}" if vehicule else "", small_gray),
                Paragraph(f"Km : {devis.vehicule_km or '-'}", small_gray),
            ]
        ]
    ]
    cv_table = Table([[cv_data[0][0], cv_data[0][1]]], colWidths=[W*0.5, W*0.5])
    cv_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (0, 0), 0.5, MID_GRAY),
        ("BOX", (1, 0), (1, 0), 0.5, MID_GRAY),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(cv_table)
    story.append(Spacer(1, 5*mm))

    # ── LIGNES PAR TYPE ──────────────────────────────────────
    TYPE_LABELS = {
        "piece": "PIÈCES DE RECHANGE",
        "main_oeuvre": "MAIN D'ŒUVRE",
        "peinture": "PEINTURE",
        "forfait": "FORFAITS / DIVERS",
    }

    lignes_by_type = {}
    for l in devis.lignes:
        lignes_by_type.setdefault(l.type, []).append(l)

    for typ, label in TYPE_LABELS.items():
        lignes = lignes_by_type.get(typ, [])
        if not lignes:
            continue

        story.append(Paragraph(label, style(f"sec_{typ}", fontSize=9, fontName="Helvetica-Bold",
                                             textColor=colors.white, backColor=MEKANO_DARK)))
        story.append(Spacer(1, 1*mm))

        col_w = [25*mm, W - 25*mm - 18*mm - 18*mm - 20*mm - 22*mm, 18*mm, 18*mm, 20*mm, 22*mm]
        table_data = [[
            Paragraph("Réf.", bold_style),
            Paragraph("Désignation", bold_style),
            Paragraph("Qté", style("th_r", fontName="Helvetica-Bold", alignment=TA_RIGHT)),
            Paragraph("PU HT", style("th_r2", fontName="Helvetica-Bold", alignment=TA_RIGHT)),
            Paragraph("Remise", style("th_r3", fontName="Helvetica-Bold", alignment=TA_RIGHT)),
            Paragraph("Total HT", style("th_r4", fontName="Helvetica-Bold", alignment=TA_RIGHT)),
        ]]

        for l in lignes:
            remise_str = f"{float(l.remise_pct):.0f}%" if l.remise_pct and float(l.remise_pct) > 0 else "-"
            table_data.append([
                Paragraph(l.reference or "", small_gray),
                Paragraph(l.designation or "", normal),
                Paragraph(f"{float(l.quantite):.2f}", style("td_r", alignment=TA_RIGHT, fontSize=9)),
                Paragraph(f"{float(l.prix_unitaire):.2f}", style("td_r2", alignment=TA_RIGHT, fontSize=9)),
                Paragraph(remise_str, style("td_r3", alignment=TA_RIGHT, fontSize=9)),
                Paragraph(f"{float(l.total_ht):.2f}", style("td_r4", alignment=TA_RIGHT, fontSize=9, fontName="Helvetica-Bold")),
            ])

        t = Table(table_data, colWidths=col_w, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, MEKANO_BLUE),
            ("LINEBELOW", (0, 1), (-1, -1), 0.3, MID_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)
        story.append(Spacer(1, 3*mm))

    # ── TOTAUX ───────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GRAY, spaceBefore=2, spaceAfter=4))

    def tot_row(label, val, bold=False, big=False):
        ls = total_style if big else (bold_style if bold else normal)
        return [
            "",
            Paragraph(label, ls),
            Paragraph(_fmt_chf(val), style("tot_val", alignment=TA_RIGHT,
                                            fontName="Helvetica-Bold" if (bold or big) else "Helvetica",
                                            fontSize=11 if big else 9,
                                            textColor=MEKANO_BLUE if big else colors.black))
        ]

    tot_data = []
    if float(devis.sous_total_pieces_ht or 0) > 0:
        tot_data.append(tot_row("Pièces de rechange HT", devis.sous_total_pieces_ht))
    if float(devis.petites_fournitures_ht or 0) > 0:
        pf_pct = float(devis.petites_fournitures_pct or 4)
        tot_data.append(tot_row(f"+ {pf_pct:.0f}% petites fournitures", devis.petites_fournitures_ht))
    if float(devis.sous_total_mo_ht or 0) > 0:
        tot_data.append(tot_row("Main d'œuvre HT", devis.sous_total_mo_ht))
    if float(devis.sous_total_peinture_ht or 0) > 0:
        tot_data.append(tot_row("Peinture HT", devis.sous_total_peinture_ht))
    if float(devis.sous_total_forfait_ht or 0) > 0:
        tot_data.append(tot_row("Forfaits / Divers HT", devis.sous_total_forfait_ht))

    tot_data.append(tot_row("Total HT", devis.total_ht, bold=True))
    tva_pct = float(devis.taux_tva or 8.1)
    tot_data.append(tot_row(f"TVA ({tva_pct:.1f}%)", devis.montant_tva))
    tot_data.append(tot_row("TOTAL TTC", devis.total_ttc, big=True))

    tot_table = Table(tot_data, colWidths=[W*0.45, W*0.33, W*0.22])
    tot_table.setStyle(TableStyle([
        ("LINEABOVE", (1, len(tot_data)-3), (2, len(tot_data)-3), 0.5, MID_GRAY),
        ("LINEABOVE", (1, len(tot_data)-1), (2, len(tot_data)-1), 1.5, MEKANO_BLUE),
        ("BACKGROUND", (1, len(tot_data)-1), (2, len(tot_data)-1), LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (2, 0), (2, -1), 4),
    ]))
    story.append(tot_table)
    story.append(Spacer(1, 5*mm))

    # ── NOTES + CONDITIONS ───────────────────────────────────
    if devis.notes_client:
        story.append(Paragraph("Notes", h2_style))
        story.append(Paragraph(devis.notes_client, normal))
        story.append(Spacer(1, 3*mm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY, spaceAfter=3))
    conditions = devis.conditions or "Devis valable 30 jours. Prix sous réserve de modification."
    story.append(Paragraph(conditions, small_gray))
    story.append(Spacer(1, 8*mm))

    # ── SIGNATURE ────────────────────────────────────────────
    sig_data = [[
        Table([
            [Paragraph("Signature client", small_gray)],
            [Paragraph("Date : _______________", small_gray)],
            [Spacer(1, 8*mm)],
            [HRFlowable(width=60*mm, thickness=0.5, color=MID_GRAY)],
        ]),
        Table([
            [Paragraph(f"Fait à {garage.localite or ''}, le {_fmt_date(devis.date_creation)}", small_gray)],
            [Spacer(1, 8*mm)],
            [HRFlowable(width=60*mm, thickness=0.5, color=MID_GRAY)],
            [Paragraph(f"Pour {garage.nom}", small_gray)],
        ]),
    ]]
    sig_table = Table(sig_data, colWidths=[W*0.5, W*0.5])
    story.append(sig_table)

    # ── TVA FOOTER ───────────────────────────────────────────
    story.append(Spacer(1, 4*mm))
    tva_info = f"N° TVA : {garage.numero_tva}" if garage.numero_tva else ""
    story.append(Paragraph(
        f"<font size='7' color='gray'>{tva_info} — Généré par Mekano | mekano.ch</font>",
        style("footer", alignment=TA_CENTER, fontSize=7, textColor=TEXT_GRAY)
    ))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
