import json
import tempfile
import yaml
from pathlib import Path
from sotd.extract.run import run_extraction_for_month


def test_run_extraction_for_month_valid(monkeypatch):
    comments = [
        {"id": "1", "body": "* **Razor:** Blackbird"},
        {"id": "2", "body": "* **Blade:** Feather"},
        {"id": "3", "body": "No product listed here"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "data/comments/2025-04.json"
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"data": comments}, f, ensure_ascii=False)

        monkeypatch.chdir(tmpdir)
        result = run_extraction_for_month("2025-04")

        assert result is not None

        assert result["meta"]["shave_count"] == 2
        assert result["meta"]["skipped_count"] == 1
        assert result["meta"]["comment_count"] == 3
        assert result["meta"]["field_coverage"]["razor"] == 1
        assert result["meta"]["field_coverage"]["blade"] == 1
        assert len(result["data"]) == 2
        assert len(result["skipped"]) == 1

        # Check that extracted data has structured format
        razor_data = result["data"][0]
        blade_data = result["data"][1]

        assert "razor" in razor_data
        assert razor_data["razor"]["original"] == "Blackbird"
        assert razor_data["razor"]["normalized"] == "Blackbird"

        assert "blade" in blade_data
        assert blade_data["blade"]["original"] == "Feather"
        assert blade_data["blade"]["normalized"] == "Feather"


def test_run_extraction_for_month_file_not_found():
    result = run_extraction_for_month("1900-01")
    assert result is None


def test_run_extraction_for_month_with_normalization(monkeypatch):
    """Test that normalization works correctly during extraction."""
    comments = [
        {"id": "1", "body": "* **Razor:** Blackbird $DOORKNOB"},
        {"id": "2", "body": "* **Blade:** Feather (3x)"},
        {"id": "3", "body": "* **Soap:** Tabac (sample)"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create data directory structure
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir(parents=True)

        # Create competition tags file in the right location
        competition_tags = {"strip_tags": ["DOORKNOB", "CNC", "ARTISTCLUB"], "preserve_tags": []}
        tags_path = Path(tmpdir) / "data/competition_tags.yaml"
        with open(tags_path, "w", encoding="utf-8") as f:
            yaml.dump(competition_tags, f)

        # Create comments file
        path = data_dir / "comments/2025-04.json"
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"data": comments}, f, ensure_ascii=False)

        monkeypatch.chdir(tmpdir)
        result = run_extraction_for_month("2025-04")

        assert result is not None
        assert len(result["data"]) == 3

        # Check normalization results
        razor_data = result["data"][0]
        blade_data = result["data"][1]
        soap_data = result["data"][2]

        # Razor: competition tags should be stripped
        assert razor_data["razor"]["original"] == "Blackbird $DOORKNOB"
        assert razor_data["razor"]["normalized"] == "Blackbird"

        # Blade: usage count should be stripped
        assert blade_data["blade"]["original"] == "Feather (3x)"
        assert blade_data["blade"]["normalized"] == "Feather"

        # Soap: sample marker should be stripped
        assert soap_data["soap"]["original"] == "Tabac (sample)"
        assert soap_data["soap"]["normalized"] == "Tabac"


def test_blade_normalization_country_origin(monkeypatch):
    """Test that country of origin patterns are normalized out during blade extraction."""
    comments = [
        {"id": "1", "body": "* **Blade:** Astra Green (Indian)"},
        {"id": "2", "body": "* **Blade:** Gillette Platinum (Russia)"},
        {"id": "3", "body": "* **Blade:** Wilkinson Sword (Made in Germany)"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "data/comments/2025-04.json"
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"data": comments}, f, ensure_ascii=False)

        monkeypatch.chdir(tmpdir)
        result = run_extraction_for_month("2025-04")

        assert result is not None
        assert len(result["data"]) == 3

        # Check that country of origin patterns are normalized out
        blade_data_1 = result["data"][0]
        blade_data_2 = result["data"][1]
        blade_data_3 = result["data"][2]

        # Astra Green (Indian) -> Astra Green
        assert blade_data_1["blade"]["original"] == "Astra Green (Indian)"
        assert blade_data_1["blade"]["normalized"] == "Astra Green"

        # Gillette Platinum (Russia) -> Gillette Platinum
        assert blade_data_2["blade"]["original"] == "Gillette Platinum (Russia)"
        assert blade_data_2["blade"]["normalized"] == "Gillette Platinum"

        # Wilkinson Sword (Made in Germany) -> Wilkinson Sword
        assert blade_data_3["blade"]["original"] == "Wilkinson Sword (Made in Germany)"
        assert blade_data_3["blade"]["normalized"] == "Wilkinson Sword"


def test_blade_normalization_decimal_usage_counts(monkeypatch):
    """Test that decimal usage count patterns are normalized out during blade extraction."""
    comments = [
        {
            "id": "1",
            "body": "* **Blade:** Astra - SP Green [3.5] / Gillette 7 O'Clock SharpEdge [.5]",
        },
        {"id": "2", "body": "* **Blade:** Gillette Slim Adjustable (I 2) [2.5]"},
        {"id": "3", "body": "* **Blade:** Personna Super (1.5)"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "data/comments/2025-04.json"
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"data": comments}, f, ensure_ascii=False)

        monkeypatch.chdir(tmpdir)
        result = run_extraction_for_month("2025-04")

        assert result is not None
        assert len(result["data"]) == 3

        # Check that decimal usage count patterns are normalized out
        blade_data_1 = result["data"][0]
        blade_data_2 = result["data"][1]
        blade_data_3 = result["data"][2]

        # Astra - SP Green [3.5] / Gillette 7 O'Clock SharpEdge [.5] ->
        # Astra - SP Green / Gillette 7 O'Clock SharpEdge
        original_1 = "Astra - SP Green [3.5] / Gillette 7 O'Clock SharpEdge [.5]"
        assert blade_data_1["blade"]["original"] == original_1
        assert (
            blade_data_1["blade"]["normalized"] == "Astra - SP Green / Gillette 7 O'Clock SharpEdge"
        )

        # Gillette Slim Adjustable (I 2) [2.5] -> Gillette Slim Adjustable (I 2)
        original_2 = "Gillette Slim Adjustable (I 2) [2.5]"
        assert blade_data_2["blade"]["original"] == original_2
        assert blade_data_2["blade"]["normalized"] == "Gillette Slim Adjustable (I 2)"

        # Personna Super (1.5) -> Personna Super
        original_3 = "Personna Super (1.5)"
        assert blade_data_3["blade"]["original"] == original_3
        assert blade_data_3["blade"]["normalized"] == "Personna Super"


def test_blade_normalization_hash_usage_counts(monkeypatch):
    """Test that hash usage count patterns are normalized out during blade extraction."""
    comments = [
        {"id": "1", "body": "* **Blade:** Gillette Silver Blue (#3)"},
        {"id": "2", "body": "* **Blade:** Feather (#12)"},
        {"id": "3", "body": "* **Blade:** Astra (shave #5)"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "data/comments/2025-04.json"
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"data": comments}, f, ensure_ascii=False)

        # Create competition tags file in the right location
        competition_tags = {"strip_tags": ["DOORKNOB", "CNC", "ARTISTCLUB"], "preserve_tags": []}
        tags_path = Path(tmpdir) / "data/competition_tags.yaml"
        with open(tags_path, "w", encoding="utf-8") as f:
            yaml.dump(competition_tags, f)

        monkeypatch.chdir(tmpdir)
        result = run_extraction_for_month("2025-04")

        assert result is not None
        assert len(result["data"]) == 3

        # Check that hash usage count patterns are normalized out
        blade_data_1 = result["data"][0]
        blade_data_2 = result["data"][1]
        blade_data_3 = result["data"][2]

        # Gillette Silver Blue (#3) -> Gillette Silver Blue
        assert blade_data_1["blade"]["original"] == "Gillette Silver Blue (#3)"
        assert blade_data_1["blade"]["normalized"] == "Gillette Silver Blue"

        # Feather (#12) -> Feather
        assert blade_data_2["blade"]["original"] == "Feather (#12)"
        assert blade_data_2["blade"]["normalized"] == "Feather"

        # Astra (shave #5) -> Astra
        assert blade_data_3["blade"]["original"] == "Astra (shave #5)"
        assert blade_data_3["blade"]["normalized"] == "Astra"


def test_blade_normalization_asterisk_stripping(monkeypatch):
    """Test that asterisks are stripped during blade normalization."""
    comments = [
        {"id": "1", "body": "* **Blade:** * **Gillette - Nacet** (Marathon) (541)"},
        {"id": "2", "body": "* **Blade:** Razo*Rock Mission"},
        {"id": "3", "body": "* **Blade:** * **Timeless - Stainless Steel .68** Open Comb"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "data/comments/2025-04.json"
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"data": comments}, f, ensure_ascii=False)

        # Create competition tags file in the right location
        competition_tags = {"strip_tags": ["DOORKNOB", "CNC", "ARTISTCLUB"], "preserve_tags": []}
        tags_path = Path(tmpdir) / "data/competition_tags.yaml"
        with open(tags_path, "w", encoding="utf-8") as f:
            yaml.dump(competition_tags, f)

        monkeypatch.chdir(tmpdir)
        result = run_extraction_for_month("2025-04")

        assert result is not None
        assert len(result["data"]) == 3

        # Check that asterisks are stripped
        blade_data_1 = result["data"][0]
        blade_data_2 = result["data"][1]
        blade_data_3 = result["data"][2]

        # * **Gillette - Nacet** (Marathon) (541) -> Gillette - Nacet (Marathon)
        assert blade_data_1["blade"]["original"] == "* **Gillette - Nacet** (Marathon) (541)"
        assert blade_data_1["blade"]["normalized"] == "Gillette - Nacet (Marathon)"

        # Razo*Rock Mission -> RazoRock Mission
        assert blade_data_2["blade"]["original"] == "Razo*Rock Mission"
        assert blade_data_2["blade"]["normalized"] == "RazoRock Mission"

        # * **Timeless - Stainless Steel .68** Open Comb -> Timeless - Stainless Steel .68 Open Comb
        assert blade_data_3["blade"]["original"] == "* **Timeless - Stainless Steel .68** Open Comb"
        assert blade_data_3["blade"]["normalized"] == "Timeless - Stainless Steel .68 Open Comb"
