import pytest
import yaml
from sotd.match.base_matcher import BaseMatcher


def write_temp_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


class TestBaseMatcher:
    """Test cases for BaseMatcher competition tag stripping."""

    @pytest.fixture
    def temp_catalog(self, tmp_path):
        catalog = {"TestBrand": {"TestModel": {"patterns": ["test"]}}}
        catalog_path = tmp_path / "razors.yaml"
        write_temp_yaml(catalog_path, catalog)
        return catalog_path

    @pytest.fixture
    def temp_tags(self, tmp_path):
        tags = {
            "strip_tags": ["FLIPTOP", "CNC", "STAINLESSLESS", "RAINBOW", "REVENANT", "MACHINEAGE"],
            "preserve_tags": ["MODERNGEM", "KAMISORI"],
        }
        tags_path = tmp_path / "competition_tags.yaml"
        write_temp_yaml(tags_path, tags)
        return tags_path

    def make_matcher(self, catalog_path, tags_path):
        class TempMatcher(BaseMatcher):
            def _load_competition_tags(self):
                return yaml.safe_load(open(tags_path, "r", encoding="utf-8"))

        return TempMatcher(catalog_path, "razor")

    def test_strip_competition_tags_basic(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        input_text = "EldrormR Industries MM24 $FLIPTOP $MODERNGEM $REVENANT"
        expected = "EldrormR Industries MM24 $MODERNGEM"
        result = matcher.normalize(input_text)
        assert result == expected

    def test_strip_competition_tags_preserves_useful_tags(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        input_text = "GEM Micromatic $MACHINEAGE $MODERNGEM"
        expected = "GEM Micromatic $MODERNGEM"
        result = matcher.normalize(input_text)
        assert result == expected

    def test_strip_competition_tags_multiple_spaces(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        input_text = "Blackland  Blackbird  $CNC  $STAINLESSLESS"
        expected = "Blackland Blackbird"
        result = matcher.normalize(input_text)
        assert result == expected

    def test_strip_competition_tags_case_insensitive(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        input_text = "Wolfman WR2 $cnc $stainlessless"
        expected = "Wolfman WR2"
        result = matcher.normalize(input_text)
        assert result == expected

    def test_strip_competition_tags_no_tags(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        input_text = "Merkur 34C"
        expected = "Merkur 34C"
        result = matcher.normalize(input_text)
        assert result == expected

    def test_strip_competition_tags_empty_string(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        result = matcher.normalize("")
        assert result == ""

    def test_strip_competition_tags_none_input(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        result = matcher.normalize(None)
        assert result is None

    def test_strip_competition_tags_with_backticks(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        input_text = "Blackland Razors - Blackbird `$CNC`"
        expected = "Blackland Razors - Blackbird"
        result = matcher.normalize(input_text)
        assert result == expected

    def test_strip_competition_tags_with_asterisks(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        input_text = "Alpha Shaving Works - Lone Star Outlaw **$RAINBOW**"
        expected = "Alpha Shaving Works - Lone Star Outlaw"
        result = matcher.normalize(input_text)
        assert result == expected

    def test_strip_competition_tags_partial_matches_preserved(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        input_text = "GEMINI Razor $FLIPTOP"
        expected = "GEMINI Razor"
        result = matcher.normalize(input_text)
        assert result == expected

    def test_strip_competition_tags_unknown_tags_preserved(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        input_text = "Wolfman WR2 $UNKNOWN_TAG $CNC"
        expected = "Wolfman WR2 $UNKNOWN_TAG"
        result = matcher.normalize(input_text)
        assert result == expected

    def test_strip_competition_tags_mixed_known_unknown(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        input_text = "Blackland Blackbird $CNC $STAINLESSLESS $SOMETHING_ELSE $FLIPTOP"
        expected = "Blackland Blackbird $SOMETHING_ELSE"
        result = matcher.normalize(input_text)
        assert result == expected

    def test_strip_competition_tags_preserve_tags_work(self, temp_catalog, temp_tags):
        matcher = self.make_matcher(temp_catalog, temp_tags)
        input_text = "Feather Artist Club $KAMISORI $MACHINEAGE"
        expected = "Feather Artist Club $KAMISORI"
        result = matcher.normalize(input_text)
        assert result == expected
