"""Módulo para exportaciones profesionales (PDF/Excel/CSV)."""
import csv
from pathlib import Path

def export_sales_csv(data: list, dest: Path) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # assume data is list of rows
            for row in data:
                writer.writerow(row)
        return True
    except Exception:
        return False


def export_inventory_excel(data: list, dest: Path) -> bool:
    try:
        # openpyxl may not be installed; create minimal csv if missing
        try:
            from openpyxl import Workbook
        except ImportError:
            return export_sales_csv(data, dest.with_suffix(".csv"))
        wb = Workbook()
        ws = wb.active
        for row in data:
            ws.append(row)
        wb.save(dest)
        return True
    except Exception:
        return False


def export_report_pdf(text_lines: list, dest: Path) -> bool:
    try:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            # fallback to text file
            with open(dest.with_suffix(".txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(text_lines))
            return True
        c = canvas.Canvas(str(dest), pagesize=letter)
        width, height = letter
        y = height - 40
        for line in text_lines:
            c.drawString(40, y, str(line))
            y -= 14
            if y < 40:
                c.showPage()
                y = height - 40
        c.save()
        return True
    except Exception:
        return False
