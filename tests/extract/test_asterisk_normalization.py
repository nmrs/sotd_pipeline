from sotd.utils.match_filter_utils import strip_asterisk_markup


class TestAsteriskNormalization:
    """Test cases for asterisk stripping and cleanup normalization."""

    def test_basic_asterisk_removal(self):
        """Test basic asterisk removal from product names."""
        assert strip_asterisk_markup("*New* King C. Gillette") == "New King C. Gillette"
        assert strip_asterisk_markup("*Limited* Feather Hi-Stainless") == (
            "Limited Feather Hi-Stainless"
        )
        assert strip_asterisk_markup("*Vintage* Gillette Fatboy") == "Vintage Gillette Fatboy"

    def test_multiple_asterisks(self):
        """Test removal of multiple asterisks."""
        assert strip_asterisk_markup("**New** Product") == "New Product"
        assert strip_asterisk_markup("***Product***") == "Product"
        assert strip_asterisk_markup("*New* Product *Limited*") == "New Product Limited"

    def test_asterisks_with_spaces(self):
        """Test asterisk removal with extra spaces."""
        assert strip_asterisk_markup("* New * Product") == "New Product"
        assert strip_asterisk_markup("*  New  *  Product") == "New Product"
        assert strip_asterisk_markup("  *New*  Product  ") == "New Product"

    def test_asterisks_in_middle(self):
        """Test asterisk removal when asterisks are in the middle of text."""
        assert strip_asterisk_markup("Product *Special* Edition") == "Product Special Edition"
        assert strip_asterisk_markup("Declaration *B2* in Mozingo handle") == (
            "Declaration B2 in Mozingo handle"
        )
        assert strip_asterisk_markup("Feather *Hi-Stainless* Blade") == "Feather Hi-Stainless Blade"

    def test_only_asterisks(self):
        """Test edge cases with only asterisks."""
        assert strip_asterisk_markup("***") == ""
        assert strip_asterisk_markup("*") == ""
        assert strip_asterisk_markup("**") == ""

    def test_no_asterisks_preserve_existing(self):
        """Test that products without asterisks are unchanged."""
        assert strip_asterisk_markup("King C. Gillette") == "King C. Gillette"
        assert strip_asterisk_markup("Feather Hi-Stainless") == "Feather Hi-Stainless"
        assert strip_asterisk_markup("Gillette Fatboy") == "Gillette Fatboy"

    def test_empty_and_whitespace(self):
        """Test empty strings and whitespace-only strings."""
        assert strip_asterisk_markup("") == ""
        assert strip_asterisk_markup("   ") == ""
        assert strip_asterisk_markup("*   *") == ""
        assert strip_asterisk_markup("  *  *  ") == ""

    def test_special_characters(self):
        """Test asterisk removal with special characters preserved."""
        assert strip_asterisk_markup("Product *with* (parentheses)") == (
            "Product with (parentheses)"
        )
        assert strip_asterisk_markup("Product *with* [brackets]") == "Product with [brackets]"
        assert strip_asterisk_markup("Product *with* - dashes") == "Product with - dashes"

    def test_unmatched_asterisks(self):
        """Test behavior with unmatched asterisks."""
        assert strip_asterisk_markup("Product*text") == "Producttext"
        assert strip_asterisk_markup("*Product") == "Product"
        assert strip_asterisk_markup("Product*") == "Product"

    def test_mixed_formatting(self):
        """Test complex mixed formatting scenarios."""
        assert (
            strip_asterisk_markup("*New* Product *Limited* Edition")
            == "New Product Limited Edition"
        )
        assert strip_asterisk_markup("**Vintage** *Rare* Product") == "Vintage Rare Product"
        assert strip_asterisk_markup("*Brand* Model *Format*") == "Brand Model Format"

    def test_case_preservation(self):
        """Test that case is preserved during asterisk removal."""
        assert strip_asterisk_markup("*NEW* King C. Gillette") == "NEW King C. Gillette"
        assert strip_asterisk_markup("*New* KING C. GILLETTE") == "New KING C. GILLETTE"
        assert strip_asterisk_markup("*new* king c. gillette") == "new king c. gillette"
