import os
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL

def format_hours_german(hours: float) -> str:
    """
    Formats hours with German decimal comma (e.g. 6.0 -> 6, 4.5 -> 4,5).
    If hours is 0, returns an empty string.
    """
    if hours == 0.0 or hours == 0:
        return ""
    if hours.is_integer():
        return str(int(hours))
    return f"{hours:.1f}".replace(".", ",")

def generate_docx(
    employee_name: str,
    personal_id: str,
    city_name: str,
    year: int,
    month: int,
    daily_entries: list[dict],   # From DB: work_date, hours_worked, start_time, end_time, break_duration, remarks
    target_hours: float,
    output_path: str = None
) -> str:
    """
    Generates the styled Tätigkeitsnachweis Word document.
    Returns the absolute path of the saved file.
    All times formatted as HH:MM, hours use German decimal comma.
    No "Wochenende" label for weekends.
    """
    if output_path is None:
        clean_name = "".join(c for c in employee_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        output_path = f"timesheet_{clean_name}_{month:02d}_{year}.docx"

    doc = Document()
    
    # 1. Page Setup (Margins: 0.6 inches top/bottom, 0.8 inches left/right)
    for section in doc.sections:
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    # 2. Configure Base Styles (Calibri 11pt)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # 3. Add Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_after = Pt(12)
    title_run = title_p.add_run("Tätigkeitsnachweis")
    title_run.font.size = Pt(20)
    title_run.font.bold = True
    
    # 4. Add Metadata Block
    metadata = [
        ("Name Mitarbeiter /-in:", employee_name),
        ("Personal Nummer:", personal_id),
        ("Stadt:", city_name)
    ]
    for idx, (label, val) in enumerate(metadata):
        p = doc.add_paragraph()
        # Set larger spacing after the last item to separate it from the table
        p.paragraph_format.space_after = Pt(4 if idx < len(metadata) - 1 else 12)
        p.paragraph_format.line_spacing = 1.15
        
        label_run = p.add_run(f"{label} ")
        label_run.bold = True
        
        value_run = p.add_run(val)
        value_run.underline = True
    
    # 5. Create Daily Table
    headers = ["Datum", "Arbeitsbeginn", "Arbeitsende", "Pause", "Arbeitszeit", "Sonstiges"]
    table = doc.add_table(rows=1, cols=6)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    
    # Header styling
    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = header_text
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.bold = True
        hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        
    col_widths = [Inches(1.2), Inches(1.1), Inches(1.1), Inches(0.9), Inches(1.1), Inches(1.5)]
    
    # Sort entries by work_date
    sorted_entries = sorted(daily_entries, key=lambda e: e.get("work_date", ""))
    total_hours_sum = 0.0

    for entry in sorted_entries:
        row_cells = table.add_row().cells
        
        # Parse work_date (supporting both ISO and German format)
        work_date = entry.get("work_date", "")
        formatted_date_str = work_date
        try:
            if '-' in work_date:
                dt = datetime.strptime(work_date, "%Y-%m-%d")
                formatted_date_str = dt.strftime("%d.%m.%Y")
            elif '.' in work_date:
                dt = datetime.strptime(work_date, "%d.%m.%Y")
                formatted_date_str = dt.strftime("%d.%m.%Y")
        except ValueError:
            pass
            
        hours_val = entry.get("hours_worked", 0.0)
        total_hours_sum += hours_val
        hours_str = format_hours_german(hours_val)
        
        # Pull other fields
        start_val = entry.get("start_time", "") if hours_val > 0.0 else ""
        end_val = entry.get("end_time", "") if hours_val > 0.0 else ""
        
        break_val = entry.get("break_duration", "")
        if hours_val == 0.0 or break_val == "00:00" or not break_val:
            break_val = ""
        
        remarks = entry.get("remarks", "")
        if remarks is None:
            remarks = ""
            
        row_data = [formatted_date_str, start_val, end_val, break_val, hours_str, remarks]
        
        for i, text in enumerate(row_data):
            row_cells[i].text = str(text)
            p = row_cells[i].paragraphs[0]
            if i < 5:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            row_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            
    # Set explicit column widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width
            
    # 6. Total Summary Block
    summary_p = doc.add_paragraph()
    summary_p.paragraph_format.space_before = Pt(12)
    summary_p.paragraph_format.space_after = Pt(16)
    
    summary_run_label = summary_p.add_run("Summe der Arbeitsstunden im Monat: ")
    summary_run_label.bold = True
    
    total_hours_formatted = f"{total_hours_sum:.1f}".replace(".", ",")
    summary_run_val = summary_p.add_run(f"{total_hours_formatted} Stunden")
    summary_run_val.underline = True
    
    # 7. Footer Sign-off Section
    footer_p = doc.add_paragraph()
    footer_p.paragraph_format.space_before = Pt(16)
    footer_p.add_run("Datum: ______________________")
    footer_p.add_run("\t\t\t\t")
    footer_p.add_run("Unterschrift: ______________________")
    
    caption_p = doc.add_paragraph()
    caption_p.paragraph_format.space_before = Pt(2)
    caption_run = caption_p.add_run("Datum, Unterschrift")
    caption_run.font.size = Pt(9)
    caption_run.font.italic = True
    
    doc.save(output_path)
    return os.path.abspath(output_path)
