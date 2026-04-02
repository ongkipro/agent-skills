"""Unit tests for validate_csv.py."""

import csv
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from validate_csv import validate

TEST_DATA = os.path.join(os.path.dirname(__file__), "..", "test-data")


def csv_path(name):
    return os.path.join(TEST_DATA, name)


class TestValidateCsvAllPlatforms:
    """Every platform fixture should pass validation with zero errors."""

    PLATFORMS = [
        ("square", "square-products.csv"),
        ("woocommerce", "woocommerce-products.csv"),
        ("etsy", "etsy-products.csv"),
        ("wix", "wix-products.csv"),
        ("amazon", "amazon-products.csv"),
        ("ebay", "ebay-products.csv"),
        ("clover", "clover-products.csv"),
        ("lightspeed-r", "lightspeed-r-products.csv"),
        ("lightspeed-x", "lightspeed-x-products.csv"),
        ("google-merchant-center", "google-merchant-center-products.csv"),
    ]

    @pytest.mark.parametrize("platform,filename", PLATFORMS)
    def test_valid_csv_no_errors(self, platform, filename):
        errors, warnings, stats = validate(csv_path(filename), platform)
        assert not errors, f"{platform}: unexpected errors: {errors}"
        assert stats is not None
        assert stats["products"] > 0


class TestValidateCsvBlockingErrors:

    def test_file_not_found(self):
        errors, _, stats = validate("/nonexistent/file.csv", "square")
        assert any("not found" in e.lower() for e in errors)
        assert stats is None

    def test_unsupported_platform(self):
        errors, _, stats = validate(csv_path("square-products.csv"), "shopify-pos")
        assert any("unsupported" in e.lower() for e in errors)
        assert stats is None

    def test_missing_headers(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\nval1,val2\n")
            f.flush()
            errors, _, _ = validate(f.name, "square")
        os.unlink(f.name)
        assert any("missing required headers" in e.lower() for e in errors)

    def test_empty_csv(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Token,Item Name,Variation Name,Description,SKU\n")
            f.flush()
            errors, _, stats = validate(f.name, "square")
        os.unlink(f.name)
        assert any("no products" in e.lower() for e in errors)


class TestValidateCsvWarnings:

    def test_warns_on_zero_price(self):
        errors, warnings, _ = validate(csv_path("clover-products.csv"), "clover")
        assert any("$0" in w for w in warnings)

    def test_skipped_items_reported_in_stats(self):
        _, _, stats = validate(csv_path("square-products.csv"), "square")
        assert len(stats["skipped"]) == 1
        assert stats["skipped"][0]["reason"] == "archived"

    def test_warns_on_empty_description(self):
        """Clover items don't have descriptions in our test data."""
        _, warnings, _ = validate(csv_path("clover-products.csv"), "clover")
        assert any("empty description" in w.lower() for w in warnings)

    def test_warns_on_duplicate_skus(self):
        """Create a CSV with duplicate SKUs to test duplicate detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["Clover ID", "Name", "Price", "Price Type", "SKU", "Stock Count", "Hidden"])
            writer.writerow(["1", "Product A", "10.00", "FIXED", "DUPE-SKU", "5", "No"])
            writer.writerow(["2", "Product B", "20.00", "FIXED", "DUPE-SKU", "3", "No"])
            f.flush()
            _, warnings, _ = validate(f.name, "clover")
        os.unlink(f.name)
        assert any("duplicate sku" in w.lower() for w in warnings)
