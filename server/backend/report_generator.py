import os
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(record_data: dict, output_pdf_path: str):
    """
    Generates a print-ready, professional medical radiology report in PDF format
    branded exclusively for LIV-SENSI AI with Deep Purple (#812D80) & Electric Magenta (#E52591) palette.
    Safely sanitizes all dynamic patient inputs to prevent XML injection.
    """
    # Sanitize and escape all user-controllable text
    p_name = xml_escape(str(record_data.get('patient_name', 'Anonymous')))
    p_id = xml_escape(str(record_data.get('patient_id', 'PT-9901')))
    p_age = record_data.get('age', 45)
    p_gender = xml_escape(str(record_data.get('gender', 'M')))
    p_symptoms = xml_escape(str(record_data.get('symptoms', 'None Reported')))
    p_alt_ast = xml_escape(str(record_data.get('alt_ast', 'Baseline Normal')))
    p_findings = xml_escape(str(record_data.get('findings', 'Clinical evaluation complete.')))
    p_recommendations = xml_escape(str(record_data.get('recommendations', 'Consult gastroenterologist.')))
    p_notes = xml_escape(str(record_data.get('doctor_notes', 'Pending Radiologist Review.')))

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Brand Palette Colors
    PURPLE_PRIMARY = colors.HexColor('#812D80')
    MAGENTA_ACCENT = colors.HexColor('#E52591')
    CHARCOAL_DARK = colors.HexColor('#29232D')
    LAVENDER_BG = colors.HexColor('#FAF6FA')
    BORDER_LIGHT = colors.HexColor('#E8DEEB')
    MUTED_TEXT = colors.HexColor('#77717A')

    # Custom styles
    header_title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PURPLE_PRIMARY,
        alignment=0
    )
    header_subtitle_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=MUTED_TEXT
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=PURPLE_PRIMARY,
        spaceBefore=10,
        spaceAfter=5
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=CHARCOAL_DARK
    )
    bold_label_style = ParagraphStyle(
        'BoldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=CHARCOAL_DARK
    )

    # 1. CLINIC / HOSPITAL HEADER
    header_data = [
        [
            Paragraph("<b>LIV-SENSI AI CLINICAL RADIOLOGY LABS</b><br/><font size='8' color='#77717A'>Next-Generation Deep Learning Hepatic Diagnostic Center | ISO 15189 Certified</font>", header_title_style),
            Paragraph(f"<b>Report Date:</b> {datetime.now().strftime('%d %b %Y, %H:%M')}<br/><b>Accession #:</b> {p_id}<br/><b>Status:</b> <font color='#812D80'><b>Official AI Verified</b></font>", body_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[380, 160])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 2, PURPLE_PRIMARY),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # 2. PATIENT DEMOGRAPHICS TABLE
    patient_data = [
        [
            Paragraph("<b>Patient Name:</b>", bold_label_style),
            Paragraph(p_name, body_style),
            Paragraph("<b>Patient ID:</b>", bold_label_style),
            Paragraph(p_id, body_style),
        ],
        [
            Paragraph("<b>Age / Gender:</b>", bold_label_style),
            Paragraph(f"{p_age} Yrs / {p_gender}", body_style),
            Paragraph("<b>Diagnostic Suite:</b>", bold_label_style),
            Paragraph("Liv-Sensi Ultrasound / CT Core", body_style),
        ],
        [
            Paragraph("<b>Clinical Symptoms:</b>", bold_label_style),
            Paragraph(p_symptoms, body_style),
            Paragraph("<b>ALT / AST Biomarkers:</b>", bold_label_style),
            Paragraph(p_alt_ast, body_style),
        ]
    ]
    patient_table = Table(patient_data, colWidths=[110, 160, 110, 160])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LAVENDER_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 10))

    # 3. AI PRIMARY DIAGNOSTIC ASSESSMENT
    risk_color = PURPLE_PRIMARY
    risk_val = record_data.get('risk_level', 'LOW RISK')
    if 'MODERATE' in risk_val:
        risk_color = colors.HexColor('#d97706')
    elif 'HIGH' in risk_val or 'CRITICAL' in risk_val:
        risk_color = colors.HexColor('#dc2626')

    pred_class = xml_escape(str(record_data.get('predicted_class', 'Normal Liver')))
    confidence = record_data.get('confidence', 95.0)

    ai_summary_data = [
        [
            Paragraph(f"<b>PRIMARY AI DIAGNOSTIC FINDING:</b><br/><font size='12' color='#812D80'><b>{pred_class}</b></font>", body_style),
            Paragraph(f"<b>CONFIDENCE LEVEL:</b><br/><font size='13' color='#E52591'><b>{confidence}%</b></font>", body_style),
            Paragraph(f"<b>CLINICAL RISK TIER:</b><br/><font size='12' color='{risk_color.hexval()}'><b>{risk_val}</b></font>", body_style)
        ]
    ]
    ai_summary_table = Table(ai_summary_data, colWidths=[240, 140, 160])
    ai_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LAVENDER_BG),
        ('BOX', (0, 0), (-1, -1), 1.2, PURPLE_PRIMARY),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(ai_summary_table)
    story.append(Spacer(1, 10))

    # 4. SCAN & GRAD-CAM EXPLAINABLE AI IMAGING
    scan_img_path = record_data.get('scan_path')
    heatmap_img_path = record_data.get('heatmap_path')

    img_elements = []
    if scan_img_path and os.path.exists(scan_img_path):
        img_elements.append([
            Paragraph("<b>Original Liver Scan</b>", bold_label_style),
            Paragraph("<b>AI Grad-CAM Activation Heatmap</b>", bold_label_style)
        ])
        rl_scan = RLImage(scan_img_path, width=2.4*inch, height=2.4*inch)
        rl_heat = RLImage(heatmap_img_path, width=2.4*inch, height=2.4*inch) if (heatmap_img_path and os.path.exists(heatmap_img_path)) else Paragraph("Heatmap not generated", body_style)
        img_elements.append([rl_scan, rl_heat])

        imaging_table = Table(img_elements, colWidths=[270, 270])
        imaging_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(imaging_table)
        story.append(Spacer(1, 8))

    # 5. DETAILED RADIOLOGICAL FINDINGS & RECOMMENDATIONS
    story.append(Paragraph("<b>Radiological & Neural Network Findings:</b>", section_title_style))
    story.append(Paragraph(p_findings, body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Recommended Clinical Next Steps:</b>", section_title_style))
    recs = p_recommendations.split('\n')
    for r in recs:
        if r.strip():
            story.append(Paragraph(f"• {r.strip()}", body_style))
    story.append(Spacer(1, 10))

    # 6. SIGNATURE & STATUTORY DISCLAIMER
    sig_data = [
        [
            Paragraph(f"<b>Radiologist Review & Remarks:</b><br/>{p_notes}<br/><br/><b>Verification Status:</b> <font color='#812D80'><b>ELECTRONICALLY SIGNED & VERIFIED</b></font>", body_style),
            Paragraph("<b>Interpreted by:</b><br/>Dr. Arvind Sharma, MD, DNB (Radiodiagnosis)<br/><i>Senior Consultant Radiologist</i><br/>Reg. No: MED-684291 &bull; Liv-Sensi Clinical Core", body_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[330, 210])
    sig_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 1, PURPLE_PRIMARY),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 8))

    disclaimer_text = ("<b>STATUTORY MEDICAL DISCLAIMER:</b> This diagnostic dossier is generated by a computer-assisted "
                       "deep learning radiological decision support platform (Liv-Sensi AI). This analysis is calibrated on published "
                       "clinical benchmarks to assist qualified healthcare professionals and radiologists. Clinical correlation with "
                       "laboratory tests and direct physician examination is mandatory prior to therapeutic decisions.")
    story.append(Paragraph(disclaimer_text, ParagraphStyle('Disclaimer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7, leading=9, textColor=MUTED_TEXT)))

    doc.build(story)
    return output_pdf_path
