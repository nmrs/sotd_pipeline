from sotd.enrich.enrich import enrich_blade, enrich_brush, enrich_entry


def test_enrich_blade_with_use():
    result = enrich_blade("Feather (3)")
    assert result["name"] == "Feather"
    assert result["use"] == 3
    assert result["raw"] == "Feather (3)"


def test_enrich_blade_with_xuse():
    result = enrich_blade("Feather (x3)")
    assert result["name"] == "Feather"
    assert result["use"] == 3
    assert result["raw"] == "Feather (x3)"


def test_enrich_blade_with_braces():
    result = enrich_blade("Astra SP {2}")
    assert result["name"] == "Astra SP"
    assert result["use"] == 2


def test_enrich_blade_with_brackets():
    result = enrich_blade("Nacet [7]")
    assert result["name"] == "Nacet"
    assert result["use"] == 7


def test_enrich_blade_without_use():
    result = enrich_blade("Derby Extra")
    assert result["name"] == "Derby Extra"
    assert result["use"] is None


def test_enrich_brush_with_fiber_and_knot():
    result = enrich_brush("Yaqi Timberwolf 26mm synthetic")
    assert result["name"] == "Yaqi Timberwolf 26mm synthetic"
    assert result["raw"] == "Yaqi Timberwolf 26mm synthetic"
    assert result["knot_mm"] == 26
    assert result["fiber"] == "Synthetic"


def test_enrich_brush_with_only_knot():
    result = enrich_brush("Some Brand 24mm")
    assert result["knot_mm"] == 24
    assert result["fiber"] is None


def test_enrich_brush_with_only_fiber():
    result = enrich_brush("Zenith Boar Scrubby")
    assert result["fiber"] == "Boar"
    assert result["knot_mm"] is None


def test_enrich_brush_with_neither():
    result = enrich_brush("Unknown Maker")
    assert result["fiber"] is None
    assert result["knot_mm"] is None


# Additional test functions as requested, to be placed in tests/enrich/test_enrich.py


def test_enrich_entry_full():
    entry = {"blade": "Super Blade (3)", "brush": "Synthetic 22mm"}
    enriched = enrich_entry(entry)
    assert "blade" in enriched
    assert enriched["blade"] == "Super Blade"
    assert enriched["blade_use"] == 3
    assert "brush" in enriched
    assert enriched["brush"] == "Synthetic 22mm"
    assert enriched["brush_fiber"] == "Synthetic"
    assert enriched["brush_knot_mm"] == 22


def test_enrich_entry_partial():
    entry = {"brush": "Boar 20mm"}
    enriched = enrich_entry(entry)
    assert "blade" not in enriched
    assert "brush" in enriched
    assert enriched["brush"] == "Boar 20mm"
    assert enriched["brush_fiber"] == "Boar"
    assert enriched["brush_knot_mm"] == 20


def test_enrich_entry_none():
    entry = {"handle": "Wooden Handle"}
    enriched = enrich_entry(entry)
    assert enriched == entry
