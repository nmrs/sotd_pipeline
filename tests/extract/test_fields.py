from sotd.extract import fields


def test_extract_razor_line():
    assert fields.extract_razor_line("* **Razor:** Blackbird") == "Blackbird"
    assert fields.extract_razor_line("* **razor:** Karve CB") == "Karve CB"
    assert fields.extract_razor_line("Razor: Blackbird") is None
    assert fields.extract_razor_line("* **Blade:** Astra") is None


def test_extract_blade_line():
    assert fields.extract_blade_line("* **Blade:** Feather") == "Feather"
    assert fields.extract_blade_line("* **blade:** Astra SP") == "Astra SP"
    assert fields.extract_blade_line("Blade - Feather") is None
    assert fields.extract_blade_line("* **Soap:** Tabac") is None


def test_extract_brush_line():
    assert fields.extract_brush_line("* **Brush:** Simpson T3") == "Simpson T3"
    assert fields.extract_brush_line("* **brush:** Omega Boar") == "Omega Boar"
    assert fields.extract_brush_line("* **Blade:** Nacet") is None


def test_extract_soap_line():
    assert fields.extract_soap_line("* **Soap:** B&M Seville") == "B&M Seville"
    assert fields.extract_soap_line("* **soap:** Stirling Bay Rum") == "Stirling Bay Rum"
    assert fields.extract_soap_line("* **Razor:** Game Changer") is None
