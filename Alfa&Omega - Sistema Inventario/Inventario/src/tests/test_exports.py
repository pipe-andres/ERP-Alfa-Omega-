"""Tests for export functionality."""
import sys
from pathlib import Path

# ensure project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import exporter


def test_csv_export(tmp_path):
    data = [["col1", "col2"], ["a", "b"]]
    dest = tmp_path / "ventas_20260305.csv"
    assert exporter.export_sales_csv(data, dest)
    assert dest.exists()
    txt = dest.read_text()
    assert "col1" in txt


def test_excel_export(tmp_path):
    data = [["x", "y"], [1, 2]]
    dest = tmp_path / "inventario_20260305.xlsx"
    assert exporter.export_inventory_excel(data, dest)
    # even if openpyxl not installed, fallback file should exist with csv extension
    if dest.exists():
        assert dest.suffix in (".xlsx", ".csv")
    else:
        alt = dest.with_suffix(".csv")
        assert alt.exists()


def test_pdf_export(tmp_path):
    lines = ["Reporte de ventas", "Item1"]
    dest = tmp_path / "ventas_20260305.pdf"
    assert exporter.export_report_pdf(lines, dest)
    # either pdf file or txt fallback should exist
    if dest.exists():
        assert dest.suffix == ".pdf"
    else:
        alt = dest.with_suffix(".txt")
        assert alt.exists()


def test_exports_without_optional_modules(tmp_path, monkeypatch):
    # remove pandas and reportlab from sys.modules to force fallback behavior
    monkeypatch.setitem(sys.modules, 'pandas', None)
    monkeypatch.setitem(sys.modules, 'openpyxl', None)
    monkeypatch.setitem(sys.modules, 'reportlab', None)
    # also patch submodules used directly inside exporter.export_report_pdf
    monkeypatch.setitem(sys.modules, 'reportlab.lib', None)
    monkeypatch.setitem(sys.modules, 'reportlab.lib.pagesizes', None)
    monkeypatch.setitem(sys.modules, 'reportlab.pdfgen', None)
    monkeypatch.setitem(sys.modules, 'reportlab.pdfgen.canvas', None)

    data = [["c1"]]
    csv_dest = tmp_path / "test.csv"
    assert exporter.export_sales_csv(data, csv_dest)

    xlsx_dest = tmp_path / "test.xlsx"
    # since pandas/openpyxl are unavailable, should still return True and create .csv fallback
    assert exporter.export_inventory_excel(data, xlsx_dest)
    alt = xlsx_dest.with_suffix('.csv')
    assert alt.exists()

    pdf_dest = tmp_path / "test.pdf"
    assert exporter.export_report_pdf(["a"], pdf_dest)
    alt2 = pdf_dest.with_suffix('.txt')
    assert alt2.exists()


if __name__ == "__main__":
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as td:
        p = Path(td)
        test_csv_export(p)
        test_excel_export(p)
        test_pdf_export(p)
    print("export tests passed")