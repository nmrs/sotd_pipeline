from sotd.enrich.christopher_bradley_enricher import ChristopherBradleyEnricher


class TestChristopherBradleyEnricher:
    """Test cases for ChristopherBradleyEnricher."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enricher = ChristopherBradleyEnricher()

    def test_target_field(self):
        """Test that the enricher targets the correct field."""
        assert self.enricher.target_field == "razor"

    def test_applies_to_karve_cb(self):
        """Test that the enricher applies to Karve CB razors."""
        record = {"razor": {"brand": "Karve", "model": "Christopher Bradley"}}
        assert self.enricher.applies_to(record)
        record = {"razor": {"brand": "Karve", "model": "CB"}}
        assert self.enricher.applies_to(record)

    def test_does_not_apply_to_other_brands(self):
        """Test that the enricher does not apply to non-Karve razors."""
        record = {"razor": {"brand": "Merkur", "model": "34C"}}
        assert not self.enricher.applies_to(record)

    def test_does_not_apply_to_other_karve_models(self):
        """Test that the enricher does not apply to other Karve models."""
        record = {"razor": {"brand": "Karve", "model": "Overlander"}}
        assert not self.enricher.applies_to(record)

    def test_extract_plate_level_and_type_sb(self):
        """Test plate extraction for SB series."""
        field_data = {"model": "Karve Christopher Bradley B"}
        result = self.enricher.enrich(field_data, "")
        assert result is not None
        assert result["plate_level"] == "B"
        assert result["plate_type"] == "SB"

    def test_extract_plate_level_and_type_oc(self):
        """Test plate extraction for OC series."""
        field_data = {"model": "Karve CB D OC"}
        result = self.enricher.enrich(field_data, "")
        assert result is not None
        assert result["plate_level"] == "D"
        assert result["plate_type"] == "OC"

    def test_extract_plate_level_and_type_open_comb(self):
        """Test plate extraction for open comb series."""
        field_data = {"model": "Karve CB F open comb"}
        result = self.enricher.enrich(field_data, "")
        assert result is not None
        assert result["plate_level"] == "F"
        assert result["plate_type"] == "OC"

    def test_extract_plate_level_and_type_sb_explicit(self):
        """Test plate extraction for SB series with explicit designation."""
        field_data = {"model": "Karve CB AA SB"}
        result = self.enricher.enrich(field_data, "")
        assert result is not None
        assert result["plate_level"] == "AA"
        assert result["plate_type"] == "SB"

    def test_extract_plate_level_case_insensitive(self):
        """Test plate extraction with case insensitive level."""
        field_data = {"model": "karve cb g oc"}
        result = self.enricher.enrich(field_data, "")
        assert result is not None
        assert result["plate_level"] == "G"
        assert result["plate_type"] == "OC"

    def test_extract_plate_level_and_type_default_sb(self):
        """Test plate extraction for default SB series."""
        field_data = {"model": "Karve CB E"}
        result = self.enricher.enrich(field_data, "")
        assert result is not None
        assert result["plate_level"] == "E"
        assert result["plate_type"] == "SB"

    def test_invalid_plate_level(self):
        """Test that invalid plate level is rejected."""
        field_data = {"model": "Karve CB Z OC"}
        result = self.enricher.enrich(field_data, "")
        assert result is None
        field_data = {"model": "Karve CB H"}
        result = self.enricher.enrich(field_data, "")
        assert result is None

    def test_no_plate_level(self):
        """Test that no plate level is found."""
        field_data = {"model": "Karve CB"}
        result = self.enricher.enrich(field_data, "")
        assert result is None

    def test_metadata_fields(self):
        """Test that metadata fields are correctly set."""
        field_data = {"model": "Karve CB C OC"}
        result = self.enricher.enrich(field_data, "")
        assert result is not None
        assert result["_enriched_by"] == "ChristopherBradleyEnricher"
        assert result["_extraction_source"] == "user_comment"
