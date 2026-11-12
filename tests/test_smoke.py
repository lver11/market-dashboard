"""Smoke tests: every Streamlit page must render without raising.

Network calls (yfinance, RSS, Bank of Canada) may fail in CI; the app is
expected to degrade gracefully rather than crash.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
PAGES = [ROOT / "streamlit_app.py", *sorted((ROOT / "pages").glob("*.py"))]


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_page_renders(page):
    at = AppTest.from_file(str(page), default_timeout=300)
    at.run()
    assert not at.exception, [e.value for e in at.exception]


def test_static_data_shapes():
    from utils import static_data as sd

    for evt in sd.ECONOMIC_CALENDAR:
        assert {"date", "event", "country", "importance"} <= evt.keys()
    assert all({"bank", "rate", "bias", "next_meeting"} <= r.keys() for r in sd.CENTRAL_BANK_RATES)
    assert sd.EIA_INVENTORY["report_date"]
