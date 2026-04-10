from datetime import datetime
from zoneinfo import ZoneInfo

from src.ph_client import _pt_day_boundaries


def test_pt_day_boundaries_format():
    posted_after, posted_before, ph_date = _pt_day_boundaries()
    # ISO 8601 UTC strings ending with Z
    assert posted_after.endswith("Z")
    assert posted_before.endswith("Z")
    assert len(ph_date) == 10
    assert ph_date.count("-") == 2


def test_pt_day_is_current_pt_day():
    pt = ZoneInfo("America/Los_Angeles")
    now_pt = datetime.now(pt)
    _, _, ph_date = _pt_day_boundaries()
    assert ph_date == now_pt.strftime("%Y-%m-%d")
