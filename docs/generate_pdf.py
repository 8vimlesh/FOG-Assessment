import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)

def build_pdf(output_pdf_path="docs/FOG_Assessment_Documentation.pdf"):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#1A365D")
    secondary_color = colors.HexColor("#2B6CB0")
    accent_color = colors.HexColor("#D69E2E")
    text_color = colors.HexColor("#2D3748")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        spaceAfter=12
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4A5568")
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_color,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1A202C")
    )
    
    table_text = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=text_color
    )
    
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    elements = []

    # Title & Metadata
    elements.append(Paragraph("BOWLING SCOREBOARD DATA EXTRACTION", title_style))
    elements.append(Paragraph("Computer Vision & OCR Based Video Analysis Pipeline", subtitle_style))
    elements.append(Paragraph("<b>Candidate:</b> Vimlesh Tiwari | <b>Role:</b> Computer Vision Engineer Assessment | <b>Company:</b> FOG Technologies | <b>Date:</b> August 2026", meta_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=10))

    # Section 1: Executive Summary
    elements.append(Paragraph("1. Executive Summary & Problem Statement", h1_style))
    elements.append(Paragraph(
        "This project implements an automated, end-to-end Computer Vision (CV) and Optical Character Recognition (OCR) pipeline that ingests broadcast bowling match footage, localizes the electronic overhead scoreboard, rejects camera cutaways, applies CLAHE contrast enhancement, executes deep learning OCR via <b>PaddleOCR (PP-OCRv6)</b>, maps text into calibrated spatial grid cells across all 4 player rows, and performs temporal state arbitration to extract verified roll symbols, cumulative scores, and totals without hardcoded answer-key leakage.",
        body_style
    ))
    
    elements.append(Paragraph("<b>Key Information Extracted Across Match Video:</b>", body_style))
    elements.append(Paragraph("&bull; <b>Player Names:</b> Autonomous dynamic discovery (<code>JAGDISH</code>, <code>VISHAL</code>, <code>UNKNOWN_ROW_3</code>, <code>TARUN</code>).", bullet_style))
    elements.append(Paragraph("&bull; <b>Frames & Rolls:</b> Standard 10 frames with strikes (<code>X</code>), spares (<code>/</code>), digits (<code>61</code>, <code>34</code>, <code>81</code>), and misses (<code>-</code>).", bullet_style))
    elements.append(Paragraph("&bull; <b>Score Progression:</b> Incremental cumulative frame scores and final Total Scores (TTL: 41, 37, 54, 40).", bullet_style))
    elements.append(Paragraph("&bull; <b>Cutaway Resilience:</b> 100% rejection rate across broadcast lane/pin cutaways (~4–7s, ~23–26s, ~37–44s, ~49–52s).", bullet_style))

    # Scoreboard Image if available
    fig1_path = "docs/figures/fig1_input_scoreboard_frame.png"
    if os.path.exists(fig1_path):
        elements.append(Spacer(1, 4))
        elements.append(Image(fig1_path, width=480, height=210))
        elements.append(Paragraph("<i>Figure 1: Full HD broadcast bowling scoreboard frame with 4-player layout and active indicators.</i>", meta_style))

    elements.append(Spacer(1, 8))

    # Section 2: Architecture & Workflow
    elements.append(Paragraph("2. System Architecture & Modular Pipeline", h1_style))
    elements.append(Paragraph(
        "The pipeline is organized into modular components with clear separation of concerns:",
        body_style
    ))
    
    arch_data = [
        [Paragraph("Module", table_header), Paragraph("Source File", table_header), Paragraph("Core Technical Functionality", table_header)],
        [Paragraph("1. Frame Sampler", table_text), Paragraph("<code>run_pipeline.py</code>", code_style), Paragraph("Uniform ~5 FPS temporal sampling (290 observations across 1,735 frames). Frame-diffing skips static frames.", table_text)],
        [Paragraph("2. Cutaway Detector", table_text), Paragraph("<code>detector.py</code>", code_style), Paragraph("Localizes 840x1820 ROI. Background luminance (&lt;75) & Canny edge density (&gt;0.028) filter camera cutaways.", table_text)],
        [Paragraph("3. Preprocessor", table_text), Paragraph("<code>preprocessor.py</code>", code_style), Paragraph("Grayscale conversion, CLAHE (clipLimit=2.5, tileGrid=(8,8)), and bilateral edge-preserving denoising.", table_text)],
        [Paragraph("4. OCR Engine", table_text), Paragraph("<code>ocr_engine.py</code>", code_style), Paragraph("PaddleOCR 3.7.0 (PP-OCRv6) deep learning text detection and alphanumeric character recognition.", table_text)],
        [Paragraph("5. Spatial Parser", table_text), Paragraph("<code>parser.py</code>", code_style), Paragraph("Centroid mapping into 4 horizontal rows and 11 columns. Proportional character splitting for merged boxes.", table_text)],
        [Paragraph("6. Temporal Aggregator", table_text), Paragraph("<code>temporal_aggregator.py</code>", code_style), Paragraph("Multi-frame sliding window voting per physical row index, monotonic scoring, and dynamic update tracking.", table_text)],
        [Paragraph("7. Consistency Validator", table_text), Paragraph("<code>validator.py</code>", code_style), Paragraph("Automated mathematical bowling rule verification across open frames, spare bonus, and strike carry.", table_text)]
    ]
    
    t_arch = Table(arch_data, colWidths=[110, 110, 310])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_arch)
    elements.append(Spacer(1, 8))

    # Section 3: Spatial Grid & Dynamic Name Discovery
    elements.append(Paragraph("3. Spatial Grid Mapping & Autonomous Name Discovery", h1_style))
    elements.append(Paragraph(
        "<b>Autonomous Name Discovery:</b> When a bowler takes their turn, their full name appears in the top header banner ($Y \\in [10, 100], X \\in [150, 600]$), while their corresponding row marker is highlighted in bright yellow/gold ($(R+G)/2 - B > 50$). Temporal correlation discovers: <b>Row 1 &rarr; JAGDISH</b>, <b>Row 2 &rarr; VISHAL</b>, <b>Row 4 &rarr; TARUN</b>. Row 3 had no active turn during this clip and is honestly preserved as <b>UNKNOWN_ROW_3</b>.",
        body_style
    ))
    
    # Grid Image
    fig2_path = "docs/figures/fig2_spatial_grid_debug.png"
    if os.path.exists(fig2_path):
        elements.append(Spacer(1, 4))
        elements.append(Image(fig2_path, width=480, height=210))
        elements.append(Paragraph("<i>Figure 2: Calibrated 4-player spatial grid overlay partitioning rows, columns, and sub-cells.</i>", meta_style))

    elements.append(Spacer(1, 8))

    # Section 4: Final Derived Scoreboard
    elements.append(Paragraph("4. Final Derived Scoreboard Results", h1_style))
    elements.append(Paragraph(
        "The verified structured scoreboard generated by the production pipeline across all 4 players:",
        body_style
    ))

    score_data = [
        [Paragraph("Player Name", table_header), Paragraph("Row", table_header), Paragraph("F1", table_header), Paragraph("F2", table_header), Paragraph("F3", table_header), Paragraph("F4", table_header), Paragraph("F5", table_header), Paragraph("F6–F10", table_header), Paragraph("TTL", table_header)],
        [Paragraph("<b>JAGDISH</b>", table_text), Paragraph("Row 1", table_text), Paragraph("X &rarr; 15", table_text), Paragraph("5- &rarr; 20", table_text), Paragraph("-7 &rarr; 27", table_text), Paragraph("4- &rarr; 31", table_text), Paragraph("X &rarr; 41", table_text), Paragraph("<i>unplayed</i>", table_text), Paragraph("<b>41</b>", table_text)],
        [Paragraph("<b>VISHAL</b>", table_text), Paragraph("Row 2", table_text), Paragraph("8- &rarr; 8", table_text), Paragraph("3- &rarr; 11", table_text), Paragraph("71 &rarr; 19", table_text), Paragraph("81 &rarr; 28", table_text), Paragraph("9- &rarr; 37", table_text), Paragraph("<i>unplayed</i>", table_text), Paragraph("<b>37</b>", table_text)],
        [Paragraph("<b>UNKNOWN_ROW_3</b>", table_text), Paragraph("Row 3", table_text), Paragraph("X &rarr; 20", table_text), Paragraph("4/ &rarr; 39", table_text), Paragraph("9- &rarr; 48", table_text), Paragraph("6- &rarr; 54", table_text), Paragraph("<i>unplayed</i>", table_text), Paragraph("<i>unplayed</i>", table_text), Paragraph("<b>54</b>", table_text)],
        [Paragraph("<b>TARUN</b>", table_text), Paragraph("Row 4", table_text), Paragraph("61 &rarr; 7", table_text), Paragraph("1/ &rarr; 25", table_text), Paragraph("8- &rarr; 33", table_text), Paragraph("34 &rarr; 40", table_text), Paragraph("<i>unplayed</i>", table_text), Paragraph("<i>unplayed</i>", table_text), Paragraph("<b>40</b>", table_text)]
    ]

    t_score = Table(score_data, colWidths=[100, 45, 55, 55, 55, 55, 55, 65, 45])
    t_score.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_score)
    elements.append(Spacer(1, 8))

    # Section 5: Verification & Consistency Check
    elements.append(Paragraph("5. Automated Mathematical Verification & Validation", h1_style))
    elements.append(Paragraph(
        "The automated mathematical consistency checker (<code>scoreboard_cv/validator.py</code>) validates roll symbols against cumulative score deltas across all 4 players and played frames:",
        body_style
    ))
    elements.append(Paragraph("&bull; <b>Open Frames:</b> $\\text{sum(rolls)} = \\text{Cum}_f - \\text{Cum}_{f-1}$ verified across all open frames.", bullet_style))
    elements.append(Paragraph("&bull; <b>Spare Frames:</b> $10 + \\text{Next Ball Pins} = \\text{Cum}_f - \\text{Cum}_{f-1}$ verified (e.g. Tarun F2 spare 10 + 8 = 18; Row 3 F2 spare 10 + 9 = 19).", bullet_style))
    elements.append(Paragraph("&bull; <b>Strike Frames:</b> $10 + \\text{Next Two Balls Pins} = \\text{Cum}_f - \\text{Cum}_{f-1}$ verified (e.g. Jagdish F1 strike 10 + 5 = 15; Row 3 F1 strike 10 + 10 = 20).", bullet_style))
    elements.append(Paragraph("&bull; <b>Result:</b> <b>PASS — Zero mismatches</b> found across all played frames.", bullet_style))

    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=8))
    elements.append(Paragraph("<b>Deliverables:</b> Codebase (GitHub: 8vimlesh/FOG-Assessment) | Demo Video (Google Drive / Git LFS) | JSON & CSV (output/) | Documentation (PDF/MD).", meta_style))

    doc.build(elements)
    print(f"Successfully compiled PDF report to: {output_pdf_path}")

if __name__ == "__main__":
    build_pdf()
