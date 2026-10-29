"""
Utility functions for Malaria Detection System:
1. File validation for microscopy blood smear uploads.
2. Automated PDF Laboratory Report generator using ReportLab.
"""

import io
from pathlib import Path
from PIL import Image
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files.base import ContentFile

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


# Allowed upload file extensions
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png']
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


def validate_image_file(uploaded_file):
    """
    Validates uploaded blood smear microscopy image:
    1. Checks file extension against allowed formats.
    2. Checks file size against 10MB limit.
    3. Verifies file is a genuine, uncorrupted image using Pillow.
    """
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Unsupported file format '{ext}'. Please upload a JPG, JPEG, or PNG image.")

    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError("File size exceeds 10 MB. Please upload a smaller microscopy image.")

    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        img.verify()  # Verifies image integrity
        uploaded_file.seek(0)  # Reset pointer for subsequent processing
    except Exception:
        raise ValidationError("Corrupt or invalid image file. Please upload a valid microscopy image.")


def generate_pdf_report(test_record):
    """
    Generates a PDF laboratory screening report for a given TestRecord using ReportLab.
    Returns a ContentFile containing the binary PDF content.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e3a8a'),
        alignment=1,  # Center
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4b5563'),
        alignment=1,
        spaceAfter=15,
    )
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e40af'),
        spaceBefore=10,
        spaceAfter=6,
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 9
    normal_style.leading = 13

    elements = []

    # Title & Subtitle Header
    elements.append(Paragraph("MALARIA DETECTION & SCREENING SYSTEM", title_style))
    elements.append(Paragraph("Microscopy Laboratory Decision-Support Report", subtitle_style))
    elements.append(Spacer(1, 6))

    # Test Metadata Bar
    meta_data = [
        [
            Paragraph(f"<b>Report ID:</b> {test_record.report.report_id if hasattr(test_record, 'report') else 'N/A'}", normal_style),
            Paragraph(f"<b>Test ID:</b> {test_record.test_id}", normal_style),
            Paragraph(f"<b>Date:</b> {test_record.test_date.strftime('%Y-%m-%d %H:%M')}", normal_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[2.3 * inch, 2.3 * inch, 2.3 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 10))

    # Patient Details Section
    elements.append(Paragraph("Patient Information", section_style))
    patient = test_record.patient
    patient_data = [
        [
            Paragraph(f"<b>Patient ID:</b> {patient.patient_id}", normal_style),
            Paragraph(f"<b>Full Name:</b> {patient.name}", normal_style),
        ],
        [
            Paragraph(f"<b>Age / Gender:</b> {patient.age} yrs / {patient.gender}", normal_style),
            Paragraph(f"<b>Contact:</b> {patient.contact or 'N/A'}", normal_style),
        ],
        [
            Paragraph(f"<b>Address:</b> {patient.address or 'N/A'}", normal_style),
            Paragraph(f"<b>Registered:</b> {patient.created_at.strftime('%Y-%m-%d')}", normal_style),
        ]
    ]
    patient_table = Table(patient_data, colWidths=[3.5 * inch, 3.5 * inch])
    patient_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 10))

    # Clinical Symptoms
    elements.append(Paragraph("Clinical Symptoms (Supporting Information)", section_style))
    if hasattr(test_record, 'symptoms'):
        sym = test_record.symptoms
        sym_list = sym.symptom_list
        sym_text = ", ".join(sym_list) if sym_list else "No active symptoms reported."
    else:
        sym_text = "No symptoms recorded."
    
    symptoms_data = [[Paragraph(f"<b>Recorded Symptoms:</b> {sym_text}", normal_style)]]
    symptoms_table = Table(symptoms_data, colWidths=[7.0 * inch])
    symptoms_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(symptoms_table)
    elements.append(Spacer(1, 10))

    # Screening & Prediction Results Section
    elements.append(Paragraph("Microscopy Screening & AI Inference Result", section_style))
    
    pred = getattr(test_record, 'prediction', None)
    result_text = pred.result if pred else "Pending"
    confidence_val = f"{pred.confidence_score:.1f}%" if pred else "N/A"
    model_name = pred.ml_model.name if (pred and pred.ml_model) else "Screening Classifier"

    res_color = colors.HexColor('#dc2626') if result_text == 'Parasitized' else colors.HexColor('#16a34a')

    result_p = Paragraph(f"<font color='{res_color.hexval()}'><b>{result_text.upper()}</b></font>", ParagraphStyle(
        'ResStyle', parent=styles['Heading2'], fontSize=15, leading=18
    ))
    conf_p = Paragraph(f"<b>Model Confidence:</b> {confidence_val}", normal_style)
    model_p = Paragraph(f"<b>Screening Model:</b> {model_name}", normal_style)

    # Check if blood smear image exists to include
    img_element = None
    if hasattr(test_record, 'blood_smear') and test_record.blood_smear.image:
        try:
            img_path = test_record.blood_smear.image.path
            img_element = RLImage(img_path, width=1.5 * inch, height=1.5 * inch)
        except Exception:
            img_element = Paragraph("<i>[Image not available]</i>", normal_style)

    if img_element:
        pred_data = [
            [
                img_element,
                [
                    Paragraph("<b>Screening Outcome:</b>", normal_style),
                    result_p,
                    Spacer(1, 4),
                    conf_p,
                    Spacer(1, 4),
                    model_p,
                    Spacer(1, 4),
                    Paragraph(f"<b>Inference Time:</b> {pred.inference_time_ms if pred else 0} ms", normal_style),
                ]
            ]
        ]
        pred_table = Table(pred_data, colWidths=[1.8 * inch, 5.2 * inch])
    else:
        pred_data = [
            [result_p, conf_p],
            [model_p, Paragraph(f"<b>Inference Time:</b> {pred.inference_time_ms if pred else 0} ms", normal_style)]
        ]
        pred_table = Table(pred_data, colWidths=[3.5 * inch, 3.5 * inch])

    pred_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#93c5fd')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(pred_table)
    elements.append(Spacer(1, 14))

    # Notes if any
    if test_record.notes:
        elements.append(Paragraph(f"<b>Clinical Notes:</b> {test_record.notes}", normal_style))
        elements.append(Spacer(1, 8))

    # Medical Disclaimer Block
    disclaimer_style = ParagraphStyle(
        'DisclaimerText',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#b45309'),
    )
    disclaimer_data = [
        [
            Paragraph(
                "<b>IMPORTANT MEDICAL DISCLAIMER:</b> "
                "This application is intended for educational and screening purposes. "
                "AI-generated results should not be considered a definitive medical diagnosis "
                "and must be confirmed by an appropriately qualified healthcare professional.",
                disclaimer_style
            )
        ]
    ]
    disclaimer_table = Table(disclaimer_data, colWidths=[7.0 * inch])
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fffbeb')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#fde68a')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(disclaimer_table)
    elements.append(Spacer(1, 25))

    # Signatures
    sign_data = [
        [
            Paragraph("____________________________<br/><b>Conducted By (Laboratory Technician)</b>", normal_style),
            Paragraph("____________________________<br/><b>Verified By (Medical Officer)</b>", normal_style),
        ]
    ]
    sign_table = Table(sign_data, colWidths=[3.5 * inch, 3.5 * inch])
    sign_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(sign_table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), name=f"Report_{test_record.test_id}.pdf")
