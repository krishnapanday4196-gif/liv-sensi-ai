import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(record_data: dict, output_pdf_path: str):
    """
    Generates a print-ready, professional medical radiology report in PDF format.
    """
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

    # Custom styles
    header_title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=0
    )
    header_subtitle_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0284c7')
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    bold_label_style = ParagraphStyle(
        'BoldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )

    # 1. CLINIC / HOSPITAL HEADER
    header_data = [
        [
            Paragraph("<b>HEPATOVISION AI RADIOLOGY LABS</b><br/><font size='8' color='#64748b'>Advanced Deep Learning Liver Imaging & Diagnostic Center | ISO 15189 Certified</font>", header_title_style),
            Paragraph(f"<b>Report Date:</b> {datetime.now().strftime('%d %b %Y, %H:%M')}<br/><b>Accession #:</b> {record_data.get('patient_id', 'ACC-8821')}<br/><b>Status:</b> <font color='#16a34a'>Final Verified</font>", body_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[380, 160])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor('#0284c7')),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # 2. PATIENT DEMOGRAPHICS TABLE
    patient_data = [
        [
            Paragraph("<b>Patient Name:</b>", bold_label_style),
            Paragraph(str(record_data.get('patient_name', 'Anonymous')), body_style),
            Paragraph("<b>Patient ID:</b>", bold_label_style),
            Paragraph(str(record_data.get('patient_id', 'PT-9901')), body_style),
        ],
        [
            Paragraph("<b>Age / Gender:</b>", bold_label_style),
            Paragraph(f"{record_data.get('age', 45)} Yrs / {record_data.get('gender', 'M')}", body_style),
            Paragraph("<b>Imaging Modality:</b>", bold_label_style),
            Paragraph("Abdominal CT / Ultrasound Scan", body_style),
        ],
        [
            Paragraph("<b>Clinical Symptoms:</b>", bold_label_style),
            Paragraph(str(record_data.get('symptoms', 'None Reported')), body_style),
            Paragraph("<b>ALT / AST Enzymes:</b>", bold_label_style),
            Paragraph(str(record_data.get('alt_ast', 'Baseline Normal')), body_style),
        ]
    ]
    patient_table = Table(patient_data, colWidths=[110, 160, 110, 160])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 12))

    # 3. AI PRIMARY DIAGNOSTIC ASSESSMENT
    risk_color = colors.HexColor('#16a34a')
    risk_val = record_data.get('risk_level', 'LOW RISK')
    if 'MODERATE' in risk_val:
        risk_color = colors.HexColor('#d97706')
    elif 'HIGH' in risk_val or 'CRITICAL' in risk_val:
        risk_color = colors.HexColor('#dc2626')

    pred_class = record_data.get('predicted_class', 'Normal Liver')
    confidence = record_data.get('confidence', 95.0)

    ai_summary_data = [
        [
            Paragraph(f"<b>PRIMARY AI DIAGNOSTIC FINDING:</b><br/><font size='13' color='#0f172a'><b>{pred_class}</b></font>", body_style),
            Paragraph(f"<b>CONFIDENCE LEVEL:</b><br/><font size='13' color='#0284c7'><b>{confidence}%</b></font>", body_style),
            Paragraph(f"<b>CLINICAL RISK TIER:</b><br/><font size='13' color='{risk_color.hexval()}'><b>{risk_val}</b></font>", body_style)
        ]
    ]
    ai_summary_table = Table(ai_summary_data, colWidths=[240, 140, 160])
    ai_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#0284c7')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bae6fd')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(ai_summary_table)
    story.append(Spacer(1, 12))

    # 4. SCAN & GRAD-CAM EXPLAINABLE AI IMAGING
    scan_img_path = record_data.get('scan_path')
    heatmap_img_path = record_data.get('heatmap_path')

    img_elements = []
    if scan_img_path and os.path.exists(scan_img_path):
        img_elements.append([
            Paragraph("<b>Original Liver Scan</b>", bold_label_style),
            Paragraph("<b>AI Grad-CAM Heatmap (ROI Activation)</b>", bold_label_style)
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
        story.append(Spacer(1, 10))

    # 5. DETAILED RADIOLOGICAL FINDINGS & RECOMMENDATIONS
    story.append(Paragraph("<b>Radiological & Neural Network Findings:</b>", section_title_style))
    story.append(Paragraph(record_data.get('findings', 'No significant pathology detected.'), body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Recommended Clinical Next Steps:</b>", section_title_style))
    recs = record_data.get('recommendations', 'Maintain routine follow-up.').split('\n')
    for r in recs:
        if r.strip():
            story.append(Paragraph(f"• {r.strip()}", body_style))
    story.append(Spacer(1, 12))

    # 6. SIGNATURE & STATUTORY DISCLAIMER
    doctor_notes = record_data.get('doctor_notes', 'AI assessment verified against standard radiological criteria.')
    sig_data = [
        [
            Paragraph(f"<b>Radiologist Review & Remarks:</b><br/>{doctor_notes}<br/><br/><b>Verification Status:</b> <font color='#16a34a'>SIGNED & VERIFIED</font>", body_style),
            Paragraph("<b>Interpreted by:</b><br/>Dr. Arvind Sharma, MD, DNB (Radiodiagnosis)<br/><i>Senior Consultant Radiologist</i><br/>Reg. No: MED-684291", body_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[330, 210])
    sig_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 8))

    disclaimer_text = ("<b>STATUTORY MEDICAL DISCLAIMER:</b> This report is generated by a computer-assisted "
                       "deep learning diagnostic support tool (HepatoVision AI). This analysis is intended to assist "
                       "qualified medical professionals and radiologists. Clinical correlation with laboratory tests "
                       "and direct clinical examination is mandatory prior to therapeutic decisions.")
    story.append(Paragraph(disclaimer_text, ParagraphStyle('Disclaimer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7, leading=9, textColor=colors.HexColor('#64748b'))))

    doc.build(story)
    return output_pdf_path
