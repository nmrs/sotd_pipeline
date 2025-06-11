from sotd.utils.text import preprocess_body
from sotd.extract.fields import extract_field


def test_extract_field_lines():
    cases = {
        "razor": [
            ("* **Razor:** Blackbird", "Blackbird"),
            ("* **Razor**: Blackbird", "Blackbird"),
            ("* **razor:** Karve CB", "Karve CB"),
            ("* Razor: Henson AL13", "Henson AL13"),
            ("Razor: Game Changer", "Game Changer"),
            ("* ##Razor## - Henson AL-13+", "Henson AL-13+"),
            ("* Razor - Henson Al13+", "Henson Al13+"),
            ("* **Blade:** Astra", None),
            ("- **Razor:** Blackland Vector", "Blackland Vector"),
            ("* **Razor** : Pearl L-55", "Pearl L-55"),
            ("🪒 *Razor:* Dollar Tree Safety Razor", "Dollar Tree Safety Razor"),
            (preprocess_body("\\* \\*\\*Razor:\\*\\* Gillette Superspeed"), "Gillette Superspeed"),
        ],
        "blade": [
            ("* **Blade:** Feather", "Feather"),
            ("* **Blade**: Feather", "Feather"),
            ("* **blade:** Astra SP", "Astra SP"),
            ("* Blade: Nacet(x2)", "Nacet(x2)"),
            ("Blade: GSB", "GSB"),
            ("* ##Blade## - VOLSHOD", "VOLSHOD"),
            ("* Blade - Shark Super Chrome", "Shark Super Chrome"),
            ("* **Soap:** Tabac", None),
            ("- **Blade:** Schick Proline", "Schick Proline"),
            ("* **Blade** : Gillette Winner", "Gillette Winner"),
            ("🧴 *Blade:* Dollar Tree Safety Razor", "Dollar Tree Safety Razor"),
        ],
        "brush": [
            ("* **Brush:** Simpson T3", "Simpson T3"),
            ("* **Brush**: Simpson T3", "Simpson T3"),
            ("* **brush:** Omega Boar", "Omega Boar"),
            ("* Brush: Power Ranger brush", "Power Ranger brush"),
            ("Brush: Boti White Boar", "Boti White Boar"),
            ("* ##Brush## - Yaqi Sagrada Familia", "Yaqi Sagrada Familia"),
            ("* Brush - Rocky Mountain - Badger", "Rocky Mountain - Badger"),
            ("* **Blade:** Nacet", None),
            ("- **Brush:** C&H Odin's Beard", "C&H Odin's Beard"),
            ("* **Brush** : Zenith Boar", "Zenith Boar"),
        ],
        "soap": [
            ("* **Soap:** B&M Seville", "B&M Seville"),
            ("* **Soap**: B&M Seville", "B&M Seville"),
            ("* **soap:** Stirling Bay Rum", "Stirling Bay Rum"),
            ("* Soap: Tabac", "Tabac"),
            ("Soap: Cella Red", "Cella Red"),
            ("* ##Lather## - CBL Inconceivable", "CBL Inconceivable"),
            ("* **Razor:** Game Changer", None),
            ("- **Soap:** MWF", "MWF"),
            ("* **Soap** : Arko", "Arko"),
            ("* Soap - Arko Stick", "Arko Stick"),
            # Lather variations
            ("* **Lather:** B&M Seville", "B&M Seville"),
            ("* **Lather**: B&M Seville", "B&M Seville"),
            ("* **lather:** Stirling Bay Rum", "Stirling Bay Rum"),
            ("* Lather: Tabac", "Tabac"),
            ("Lather: Cella Red", "Cella Red"),
            (
                "* ##Soap## - CBL Inconceivable",
                "CBL Inconceivable",
            ),  # Already covered Lather, making sure Soap also works with this
            ("- **Lather:** MWF", "MWF"),
            ("* **Lather** : Arko", "Arko"),
            ("* Lather - Arko Stick", "Arko Stick"),
            # Additional patterns from get_patterns for both Soap and Lather
            ("* **Soap:** Some Soap Co.", "Some Soap Co."),  # Basic with colon
            (
                "* **Lather**: Another Lather Co.",
                "Another Lather Co.",
            ),  # Basic with space after colon
            ("Soap: Yet Another Soap", "Yet Another Soap"),  # No markdown, simple case
            ("Lather: Yet Another Lather", "Yet Another Lather"),  # No markdown, simple case
            ("* ##Soap## - Special Soap", "Special Soap"),  # Double hash
            ("* ##Lather## - Special Lather", "Special Lather"),  # Double hash
            ("- **Soap:** Hyphen Soap", "Hyphen Soap"),  # Hyphen prefix
            ("- **Lather:** Hyphen Lather", "Hyphen Lather"),  # Hyphen prefix
            ("🧴 *Soap:* Emoji Soap", "Emoji Soap"),  # Emoji prefix
            ("🧴 *Lather:* Emoji Lather", "Emoji Lather"),  # Emoji prefix
            (
                preprocess_body("\\* \\*\\*Soap:\\*\\* Escaped Soap"),
                "Escaped Soap",
            ),  # Preprocessed/escaped
            (
                preprocess_body("\\* \\*\\*Lather:\\*\\* Escaped Lather"),
                "Escaped Lather",
            ),  # Preprocessed/escaped
            ("* __Soap:__ Underlined Soap", "Underlined Soap"),  # Underscore emphasis
            ("* __Lather:__ Underlined Lather", "Underlined Lather"),  # Underscore emphasis
            ("* **Soap //** Forward Slash Soap", "Forward Slash Soap"),  # Forward slash separation
            (
                "* **Lather //** Forward Slash Lather",
                "Forward Slash Lather",
            ),  # Forward slash separation
            ("‣ **Soap**: Bullet Soap", "Bullet Soap"),  # Different bullet
            ("‣ **Lather**: Bullet Lather", "Bullet Lather"),  # Different bullet
            ("* **Soap** - Dash Separated Soap", "Dash Separated Soap"),  # Dash separated
            ("* **Lather** - Dash Separated Lather", "Dash Separated Lather"),  # Dash separated
        ],
    }

    for field, tests in cases.items():
        for line, expected in tests:
            assert extract_field(line, field) == expected
