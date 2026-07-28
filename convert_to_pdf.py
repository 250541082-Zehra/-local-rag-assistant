import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

def convert_md_to_pdf(md_file_path, pdf_file_path):
    # Windows Arial fontunu Türkçe desteği için kaydet
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    font_bold_path = "C:\\Windows\\Fonts\\arialbd.ttf"
    
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('ArialTR', font_path))
        font_name = 'ArialTR'
    else:
        font_name = 'Helvetica'
        
    if os.path.exists(font_bold_path):
        pdfmetrics.registerFont(TTFont('ArialTR-Bold', font_bold_path))
        bold_font_name = 'ArialTR-Bold'
    else:
        bold_font_name = font_name

    styles = getSampleStyleSheet()
    
    # Custom stiller
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Normal'],
        fontName=bold_font_name,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0078D4"),
        spaceAfter=12
    )
    
    h1_style = ParagraphStyle(
        'H1Style',
        parent=styles['Normal'],
        fontName=bold_font_name,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#107C41"),
        spaceBefore=12,
        spaceAfter=6
    )
    
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Normal'],
        fontName=bold_font_name,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B579A"),
        spaceBefore=10,
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#202020"),
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#333333"),
        leftIndent=15,
        spaceAfter=4
    )

    doc = SimpleDocTemplate(
        pdf_file_path,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    story = []
    
    with open(md_file_path, "r", encoding="utf-8") as f:
        md_lines = f.readlines()
        
    for line in md_lines:
        line_str = line.strip()
        if not line_str:
            story.append(Spacer(1, 4))
            continue
            
        # HTML kaçış karakterlerini temizle
        line_clean = line_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Bold Markdown (**text**) -> <b>text</b>
        import re
        line_clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_clean)
        
        if line_str.startswith("# "):
            story.append(Paragraph(line_clean[2:], title_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0078D4"), spaceAfter=10))
        elif line_str.startswith("## "):
            story.append(Paragraph(line_clean[3:], h1_style))
        elif line_str.startswith("### "):
            story.append(Paragraph(line_clean[4:], h2_style))
        elif line_str.startswith("- ") or line_str.startswith("* "):
            story.append(Paragraph("• " + line_clean[2:], bullet_style))
        elif line_str.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceBefore=8, spaceAfter=8))
        else:
            story.append(Paragraph(line_clean, body_style))
            
    doc.build(story)
    print(f"[OK] PDF başarıyla dönüştürüldü: {pdf_file_path}")

if __name__ == "__main__":
    src_md = r"C:\Users\CASPER\.gemini\antigravity\brain\613ccf34-ad8c-4c12-b9cb-9e679857d230\staj_ogrenim_ve_sunum_rehberi.md"
    out_pdf = r"C:\Users\CASPER\.gemini\antigravity\brain\613ccf34-ad8c-4c12-b9cb-9e679857d230\Microsoft_Staj_RAG_Rehberi.pdf"
    convert_md_to_pdf(src_md, out_pdf)
