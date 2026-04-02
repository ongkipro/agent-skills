"""Unit tests for platform CSV parsers.

Tests the deterministic mapping logic: given a CSV, verify correct Shopify productSet payloads.
Run with: pytest agent-skills/shopify-import/tests/ -v
"""

import os
import sys

import pytest

# Add scripts dir to path so we can import parsers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from parsers import (
    parse_square,
    parse_woocommerce,
    parse_etsy,
    parse_wix,
    parse_amazon,
    parse_ebay,
    parse_clover,
    parse_lightspeed_r,
    parse_lightspeed_x,
    parse_google_merchant_center,
)

TEST_DATA = os.path.join(os.path.dirname(__file__), "..", "test-data")


def csv_path(name):
    path = os.path.join(TEST_DATA, name)
    assert os.path.exists(path), f"Test fixture not found: {path}"
    return path


def find_product(products, substring):
    """Find a product by title substring. Raises a clear error if not found."""
    matches = [p for p in products if substring in p["input"]["title"]]
    assert matches, f"No product found with '{substring}' in title. Available: {[p['input']['title'] for p in products]}"
    return matches[0]


# ============================================================
# Square
# ============================================================


class TestSquare:
    def setup_method(self):
        self.products, self.skipped = parse_square(csv_path("square-products.csv"))

    def test_product_count(self):
        assert len(self.products) == 2

    def test_skipped_archived(self):
        assert len(self.skipped) == 1
        assert self.skipped[0]["reason"] == "archived"
        assert "Vintage Espresso" in self.skipped[0]["title"]

    def test_multi_variant_product(self):
        coffee = find_product(self.products, "Pour-Over")
        inp = coffee["input"]
        assert inp["title"] == "(Square) Ceramic Pour-Over Coffee Set"
        assert inp["status"] == "DRAFT"
        assert inp["productType"] == "Coffee Equipment"
        assert inp["handle"] == "ceramic-pour-over-set"
        assert len(inp["variants"]) == 3
        assert len(inp["productOptions"]) == 2
        assert inp["productOptions"][0]["name"] == "Color"
        assert inp["productOptions"][1]["name"] == "Size"

    def test_variant_details(self):
        coffee = find_product(self.products, "Pour-Over")
        variant = coffee["input"]["variants"][0]
        assert variant["sku"] == "SQ-POUR-WHR"
        assert variant["price"] == 64.99
        assert variant["optionValues"][0] == {"optionName": "Color", "name": "White"}
        assert variant["optionValues"][1] == {"optionName": "Size", "name": "Regular"}

    def test_single_variant_product(self):
        board = find_product(self.products, "Bamboo")
        inp = board["input"]
        assert len(inp["variants"]) == 1
        assert inp["productOptions"][0]["name"] == "Title"

    def test_seo_fields(self):
        coffee = find_product(self.products, "Pour-Over")
        seo = coffee["input"]["seo"]
        assert seo["title"] == "Ceramic Pour-Over Set"
        assert "ceramic pour-over" in seo["description"].lower()

    def test_weight_parsed(self):
        coffee = find_product(self.products, "Pour-Over")
        measurement = coffee["input"]["variants"][0]["inventoryItem"]["measurement"]
        assert measurement["weight"]["unit"] == "KILOGRAMS"
        assert measurement["weight"]["value"] == 0.85

    def test_inventory_quantities(self):
        coffee = find_product(self.products, "Pour-Over")
        assert coffee["inventory"][0] == 25

    def test_barcode(self):
        coffee = find_product(self.products, "Pour-Over")
        assert coffee["input"]["variants"][0]["barcode"] == "012345678901"

    def test_cost_is_numeric(self):
        """Fix #7: Cost should be numeric, not string."""
        coffee = find_product(self.products, "Pour-Over")
        cost = coffee["input"]["variants"][0]["inventoryItem"]["cost"]
        assert isinstance(cost, float), f"Cost should be float, got {type(cost)}: {cost}"
        assert cost == 32.0


# ============================================================
# WooCommerce
# ============================================================


class TestWooCommerce:
    def setup_method(self):
        self.products, self.skipped = parse_woocommerce(csv_path("woocommerce-products.csv"))

    def test_product_count(self):
        assert len(self.products) == 2

    def test_skipped_external(self):
        assert len(self.skipped) == 1
        assert "external" in self.skipped[0]["reason"]
        assert "Partner Brand Tent" in self.skipped[0]["title"]

    def test_simple_product(self):
        compass = find_product(self.products, "Compass")
        inp = compass["input"]
        assert inp["title"] == "(WooCommerce) Brass Pocket Compass"
        assert len(inp["variants"]) == 1
        assert inp["variants"][0]["price"] == 42.0
        assert inp["productOptions"][0]["name"] == "Title"

    def test_variable_product_variants(self):
        socks = find_product(self.products, "Socks")
        assert len(socks["input"]["variants"]) == 4
        assert len(socks["input"]["productOptions"]) == 2

    def test_sale_price_mapping(self):
        socks = find_product(self.products, "Socks")
        charcoal_m = socks["input"]["variants"][0]
        assert charcoal_m["price"] == 19.99
        assert charcoal_m["compareAtPrice"] == 24.99

    def test_no_sale_price(self):
        socks = find_product(self.products, "Socks")
        fg_m = socks["input"]["variants"][2]
        assert fg_m["price"] == 24.99
        assert "compareAtPrice" not in fg_m

    def test_inventory(self):
        compass = find_product(self.products, "Compass")
        assert compass["inventory"][0] == 60

    def test_tags(self):
        socks = find_product(self.products, "Socks")
        assert "hiking" in socks["input"]["tags"]
        assert "merino" in socks["input"]["tags"]


# ============================================================
# Etsy
# ============================================================


class TestEtsy:
    def setup_method(self):
        self.products, self.skipped = parse_etsy(csv_path("etsy-products.csv"))

    def test_product_count(self):
        assert len(self.products) == 2

    def test_variant_combinations(self):
        candle = find_product(self.products, "Candle")
        assert len(candle["input"]["variants"]) == 6

    def test_options(self):
        candle = find_product(self.products, "Candle")
        assert len(candle["input"]["productOptions"]) == 2
        assert candle["input"]["productOptions"][0]["name"] == "Scent"
        assert candle["input"]["productOptions"][1]["name"] == "Size"

    def test_sku_distribution(self):
        candle = find_product(self.products, "Candle")
        skus = [v["sku"] for v in candle["input"]["variants"]]
        assert len(set(skus)) == 6
        assert "ET-CNDL-LF8" in skus

    def test_single_variant_no_variations(self):
        macrame = find_product(self.products, "Macram")
        assert len(macrame["input"]["variants"]) == 1
        assert macrame["input"]["productOptions"][0]["name"] == "Title"

    def test_tags_include_materials(self):
        candle = find_product(self.products, "Candle")
        assert "soy wax" in candle["input"]["tags"]
        assert "candle" in candle["input"]["tags"]

    def test_inventory_zero(self):
        candle = find_product(self.products, "Candle")
        assert all(q == 0 for q in candle["inventory"])


# ============================================================
# Wix
# ============================================================


class TestWix:
    def setup_method(self):
        self.products, self.skipped = parse_wix(csv_path("wix-products.csv"))

    def test_product_count(self):
        assert len(self.products) == 2

    def test_multi_variant_product(self):
        yoga = find_product(self.products, "Yoga Mat")
        assert len(yoga["input"]["variants"]) == 3
        assert len(yoga["input"]["productOptions"]) == 2
        option_names = [o["name"] for o in yoga["input"]["productOptions"]]
        assert "Color" in option_names
        assert "Size" in option_names

    def test_variant_option_values(self):
        yoga = find_product(self.products, "Yoga Mat")
        colors = [v["optionValues"][0]["name"] for v in yoga["input"]["variants"]
                  if v["optionValues"][0]["optionName"] == "Color"]
        assert "Natural" in colors
        assert "Teal" in colors

    def test_surcharge_added_to_price(self):
        yoga = find_product(self.products, "Yoga Mat")
        xl_variant = next(v for v in yoga["input"]["variants"] if v["sku"] == "WX-YOGA-NAT-XL")
        assert xl_variant["price"] == 99.0

    def test_base_price_no_surcharge(self):
        yoga = find_product(self.products, "Yoga Mat")
        nat_variant = next(v for v in yoga["input"]["variants"] if v["sku"] == "WX-YOGA-NAT")
        assert nat_variant["price"] == 89.0

    def test_single_variant_product(self):
        bands = find_product(self.products, "Resistance Band")
        assert len(bands["input"]["variants"]) == 1
        assert bands["input"]["productOptions"][0]["name"] == "Title"

    def test_handle_from_handleId(self):
        yoga = find_product(self.products, "Yoga Mat")
        assert yoga["input"]["handle"] == "wix-yoga-mat-001"

    def test_vendor(self):
        yoga = find_product(self.products, "Yoga Mat")
        assert yoga["input"]["vendor"] == "EcoFlow"

    def test_tags_from_collection_and_ribbon(self):
        bands = find_product(self.products, "Resistance Band")
        assert "Fitness" in bands["input"]["tags"]
        assert "SALE" in bands["input"]["tags"]

    def test_weight(self):
        yoga = find_product(self.products, "Yoga Mat")
        w = yoga["input"]["variants"][0]["inventoryItem"]["measurement"]["weight"]
        assert w["unit"] == "KILOGRAMS"
        assert w["value"] == 2.5


# ============================================================
# Amazon
# ============================================================


class TestAmazon:
    def setup_method(self):
        self.products, self.skipped = parse_amazon(csv_path("amazon-products.csv"))

    def test_product_count(self):
        assert len(self.products) == 2

    def test_parent_child_grouping(self):
        pitcher = find_product(self.products, "Filter Pitcher")
        assert len(pitcher["input"]["variants"]) == 3

    def test_variant_options(self):
        pitcher = find_product(self.products, "Filter Pitcher")
        option_names = [o["name"] for o in pitcher["input"]["productOptions"]]
        assert "Color" in option_names
        assert "Size" in option_names

    def test_single_product(self):
        desk = find_product(self.products, "Desk Organizer")
        assert len(desk["input"]["variants"]) == 1
        assert desk["input"]["variants"][0]["price"] == 32.99

    def test_barcode(self):
        pitcher = find_product(self.products, "Filter Pitcher")
        barcodes = [v.get("barcode") for v in pitcher["input"]["variants"]]
        assert "012345600001" in barcodes

    def test_inventory(self):
        pitcher = find_product(self.products, "Filter Pitcher")
        assert pitcher["inventory"] == [75, 45, 60]


# ============================================================
# eBay
# ============================================================


class TestEbay:
    def setup_method(self):
        self.products, self.skipped = parse_ebay(csv_path("ebay-products.csv"))

    def test_product_count(self):
        assert len(self.products) == 2

    def test_skipped_auction(self):
        assert len(self.skipped) == 1
        assert "auction" in self.skipped[0]["reason"]
        assert "Vinyl" in self.skipped[0]["title"]

    def test_variation_details_parsed(self):
        bag = find_product(self.products, "Messenger Bag")
        assert len(bag["input"]["variants"]) == 2
        option_names = [o["name"] for o in bag["input"]["productOptions"]]
        assert "Color" in option_names

    def test_single_variant(self):
        mugs = find_product(self.products, "Ceramic Mug")
        assert len(mugs["input"]["variants"]) == 1
        assert mugs["input"]["variants"][0]["price"] == 48.0


# ============================================================
# Clover
# ============================================================


class TestClover:
    def setup_method(self):
        self.products, self.skipped = parse_clover(csv_path("clover-products.csv"))

    def test_product_count(self):
        assert len(self.products) == 4

    def test_skipped_hidden(self):
        assert len(self.skipped) == 1
        assert "hidden" in self.skipped[0]["reason"]
        assert "Staff Training" in self.skipped[0]["title"]

    def test_variable_pricing_zero(self):
        mystery = find_product(self.products, "Mystery Box")
        assert mystery["input"]["variants"][0]["price"] == 0

    def test_tags(self):
        bread = find_product(self.products, "Sourdough")
        assert "fresh" in bread["input"]["tags"]
        assert "daily" in bread["input"]["tags"]

    def test_cost_is_numeric(self):
        """Fix #7: Cost should be numeric, not string."""
        bread = find_product(self.products, "Sourdough")
        cost = bread["input"]["variants"][0]["inventoryItem"]["cost"]
        assert isinstance(cost, float), f"Cost should be float, got {type(cost)}"
        assert cost == 2.25


# ============================================================
# Lightspeed R-Series
# ============================================================


class TestLightspeedR:
    def setup_method(self):
        self.products, self.skipped = parse_lightspeed_r(csv_path("lightspeed-r-products.csv"))

    def test_product_count(self):
        assert len(self.products) == 2

    def test_variant_grouping(self):
        shoe = find_product(self.products, "Trail Running")
        assert len(shoe["input"]["variants"]) == 3

    def test_options(self):
        shoe = find_product(self.products, "Trail Running")
        option_names = [o["name"] for o in shoe["input"]["productOptions"]]
        assert "Size" in option_names
        assert "Color" in option_names

    def test_single_variant(self):
        poles = find_product(self.products, "Trekking Pole")
        assert len(poles["input"]["variants"]) == 1
        assert poles["input"]["productOptions"][0]["name"] == "Title"

    def test_vendor(self):
        shoe = find_product(self.products, "Trail Running")
        assert shoe["input"]["vendor"] == "Salomon"

    def test_cost_is_numeric(self):
        """Fix #7: Cost should be numeric, not string."""
        shoe = find_product(self.products, "Trail Running")
        cost = shoe["input"]["variants"][0]["inventoryItem"]["cost"]
        assert isinstance(cost, float), f"Cost should be float, got {type(cost)}"


# ============================================================
# Lightspeed X-Series
# ============================================================


class TestLightspeedX:
    def setup_method(self):
        self.products, self.skipped = parse_lightspeed_x(csv_path("lightspeed-x-products.csv"))

    def test_product_count(self):
        assert len(self.products) == 2

    def test_variant_grouping(self):
        hoodie = find_product(self.products, "Hoodie")
        assert len(hoodie["input"]["variants"]) == 3

    def test_handle(self):
        hoodie = find_product(self.products, "Hoodie")
        assert hoodie["input"]["handle"] == "organic-cotton-hoodie"

    def test_tags(self):
        hoodie = find_product(self.products, "Hoodie")
        assert "organic" in hoodie["input"]["tags"]

    def test_single_variant(self):
        tote = find_product(self.products, "Tote")
        assert len(tote["input"]["variants"]) == 1

    def test_inventory(self):
        hoodie = find_product(self.products, "Hoodie")
        assert hoodie["inventory"] == [45, 38, 30]

    def test_cost_is_numeric(self):
        """Fix #7: Cost should be numeric, not string."""
        hoodie = find_product(self.products, "Hoodie")
        cost = hoodie["input"]["variants"][0]["inventoryItem"]["cost"]
        assert isinstance(cost, float), f"Cost should be float, got {type(cost)}"


# ============================================================
# Google Merchant Center
# ============================================================


class TestGoogleMerchantCenter:
    def setup_method(self):
        self.products, self.skipped = parse_google_merchant_center(
            csv_path("google-merchant-center-products.csv")
        )

    def test_product_count(self):
        assert len(self.products) == 2

    def test_grouped_variants(self):
        jacket = find_product(self.products, "Puffer Jacket")
        assert len(jacket["input"]["variants"]) == 3

    def test_gmc_price_parsing(self):
        jacket = find_product(self.products, "Puffer Jacket")
        blue_m = jacket["input"]["variants"][0]
        assert blue_m["price"] == 159.0
        assert blue_m["compareAtPrice"] == 189.0

    def test_no_sale_price(self):
        jacket = find_product(self.products, "Puffer Jacket")
        green_m = jacket["input"]["variants"][2]
        assert green_m["price"] == 199.0
        assert "compareAtPrice" not in green_m

    def test_single_product(self):
        thermos = find_product(self.products, "Thermos")
        assert len(thermos["input"]["variants"]) == 1
        assert thermos["input"]["variants"][0]["price"] == 34.99

    def test_weight(self):
        jacket = find_product(self.products, "Puffer Jacket")
        w = jacket["input"]["variants"][0]["inventoryItem"]["measurement"]["weight"]
        assert w["unit"] == "KILOGRAMS"
        assert w["value"] == 0.45

    def test_vendor(self):
        jacket = find_product(self.products, "Puffer Jacket")
        assert jacket["input"]["vendor"] == "GreenPeak"

    def test_tags_from_custom_labels(self):
        jacket = find_product(self.products, "Puffer Jacket")
        assert "winter-collection" in jacket["input"]["tags"]

    def test_product_type_from_google_category(self):
        thermos = find_product(self.products, "Thermos")
        assert thermos["input"]["productType"] == "Drinkware"

    def test_inventory_zero_for_gmc(self):
        jacket = find_product(self.products, "Puffer Jacket")
        assert all(q == 0 for q in jacket["inventory"])


# ============================================================
# Cross-platform invariants
# ============================================================


class TestCrossPlatformInvariants:
    """Tests that all parsers satisfy the same structural invariants."""

    PARSERS = [
        ("square", parse_square, "square-products.csv"),
        ("woocommerce", parse_woocommerce, "woocommerce-products.csv"),
        ("etsy", parse_etsy, "etsy-products.csv"),
        ("wix", parse_wix, "wix-products.csv"),
        ("amazon", parse_amazon, "amazon-products.csv"),
        ("ebay", parse_ebay, "ebay-products.csv"),
        ("clover", parse_clover, "clover-products.csv"),
        ("lightspeed-r", parse_lightspeed_r, "lightspeed-r-products.csv"),
        ("lightspeed-x", parse_lightspeed_x, "lightspeed-x-products.csv"),
        ("gmc", parse_google_merchant_center, "google-merchant-center-products.csv"),
    ]

    @pytest.mark.parametrize("name,parser,filename", PARSERS)
    def test_all_products_have_draft_status(self, name, parser, filename):
        products, _ = parser(csv_path(filename))
        for p in products:
            assert p["input"]["status"] == "DRAFT", f"{name}: product not DRAFT"

    @pytest.mark.parametrize("name,parser,filename", PARSERS)
    def test_all_products_have_title(self, name, parser, filename):
        products, _ = parser(csv_path(filename))
        for p in products:
            assert p["input"]["title"], f"{name}: product missing title"

    @pytest.mark.parametrize("name,parser,filename", PARSERS)
    def test_all_products_have_options(self, name, parser, filename):
        products, _ = parser(csv_path(filename))
        for p in products:
            assert len(p["input"]["productOptions"]) >= 1, f"{name}: missing productOptions"
            for opt in p["input"]["productOptions"]:
                assert opt["name"], f"{name}: option missing name"
                assert len(opt["values"]) >= 1, f"{name}: option has no values"

    @pytest.mark.parametrize("name,parser,filename", PARSERS)
    def test_all_variants_have_option_values(self, name, parser, filename):
        products, _ = parser(csv_path(filename))
        for p in products:
            for v in p["input"]["variants"]:
                assert len(v["optionValues"]) >= 1, f"{name}: variant missing optionValues"

    @pytest.mark.parametrize("name,parser,filename", PARSERS)
    def test_variant_count_matches_inventory(self, name, parser, filename):
        products, _ = parser(csv_path(filename))
        for p in products:
            assert len(p["inventory"]) == len(p["input"]["variants"]), \
                f"{name}: inventory count doesn't match variant count"

    @pytest.mark.parametrize("name,parser,filename", PARSERS)
    def test_max_3_options(self, name, parser, filename):
        products, _ = parser(csv_path(filename))
        for p in products:
            assert len(p["input"]["productOptions"]) <= 3, f"{name}: more than 3 options"

    @pytest.mark.parametrize("name,parser,filename", PARSERS)
    def test_prices_non_negative(self, name, parser, filename):
        products, _ = parser(csv_path(filename))
        for p in products:
            for v in p["input"]["variants"]:
                assert v["price"] >= 0, f"{name}: negative price"

    @pytest.mark.parametrize("name,parser,filename", PARSERS)
    def test_compare_at_price_greater_than_price(self, name, parser, filename):
        products, _ = parser(csv_path(filename))
        for p in products:
            for v in p["input"]["variants"]:
                if "compareAtPrice" in v:
                    assert v["compareAtPrice"] > v["price"], \
                        f"{name}: compareAtPrice not greater than price"

    @pytest.mark.parametrize("name,parser,filename", PARSERS)
    def test_cost_is_numeric_when_present(self, name, parser, filename):
        """Fix #7: Cost should always be numeric (float), never a string."""
        products, _ = parser(csv_path(filename))
        for p in products:
            for v in p["input"]["variants"]:
                cost = v.get("inventoryItem", {}).get("cost")
                if cost is not None:
                    assert isinstance(cost, (int, float)), \
                        f"{name}: cost should be numeric, got {type(cost)}: {cost}"
