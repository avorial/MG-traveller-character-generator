"""PDF sheet presentation regressions."""

from app.engine.pdf_sheet import career_label


def test_core_career_labels_use_current_ids():
    assert career_label("marine", "") == "Marines"
    assert career_label("scout", "") == "Scouts"
    assert career_label("marine", "support") == "Marines / Support"
