from src.services.reports import kardex_rows
from src.services.inventory import add_product

def test_kardex_smoke():
    # Ensure product exists and kardex runs without exceptions
    add_product('R001','ReporteProd','CatR',1.0,1)
    rows, summary = kardex_rows('R001')
    assert isinstance(rows, list)
    assert isinstance(summary, dict)
