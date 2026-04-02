#!/usr/bin/env python3
"""Tophat script — imports all platform test CSVs into a Shopify dev store.

Usage:
  1. Create a dev store at https://partners.shopify.com → Stores → Add store → Development store
  2. Create a custom app: Settings → Apps → Develop apps → Create app
     Scopes needed: write_products, read_products, write_inventory, read_inventory, read_locations
  3. Install the app and copy the Admin API access token
  4. Run:

     export SHOPIFY_STORE=your-store.myshopify.com
     export SHOPIFY_ADMIN_TOKEN=shpat_xxxxxxxxxxxxx
     python3 agent-skills/shopify-import/scripts/testing/tophat.py

  5. Verify at: https://admin.shopify.com/store/<your-store>/products

Expected results:
  - 23 products created (43 variants) across all 10 platforms
  - 4 products correctly skipped (1 archived, 1 external, 1 auction, 1 hidden)
  - All products set to DRAFT status
  - Inventory quantities set where the source platform provides them
  - Product names prefixed with platform: (Square), (WooCommerce), (Etsy), etc.
"""

import os
import sys
import time

# Add scripts/ dir to path for parsers and shopify_api
# Add testing/ dir for shopify_api and scripts/ dir for parsers
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from parsers import (
    parse_square, parse_woocommerce, parse_etsy, parse_wix,
    parse_amazon, parse_ebay, parse_clover,
    parse_lightspeed_r, parse_lightspeed_x, parse_google_merchant_center,
)
from shopify_api import (
    get_credentials, get_location_id, create_product, set_inventory,
    ShopifyAPIError, MissingCredentialsError,
)


def main():
    try:
        store, token = get_credentials()
    except MissingCredentialsError as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(f"🏪 Store: {store}")

    location_id = None
    location_result = get_location_id(store, token)
    if location_result:
        location_id, location_name = location_result
        print(f"📍 Location: {location_name} ({location_id})")
    else:
        print("⚠️  Could not fetch location. Inventory quantities will be skipped.")
        print("  → Add read_locations scope to your app and reinstall.")
    print()

    test_dir = os.path.join(os.path.dirname(__file__), "..", "..", "test-data")

    platforms = [
        ("Square", parse_square, "square-products.csv"),
        ("WooCommerce", parse_woocommerce, "woocommerce-products.csv"),
        ("Etsy", parse_etsy, "etsy-products.csv"),
        ("Wix", parse_wix, "wix-products.csv"),
        ("Amazon", parse_amazon, "amazon-products.csv"),
        ("eBay", parse_ebay, "ebay-products.csv"),
        ("Clover", parse_clover, "clover-products.csv"),
        ("Lightspeed R-Series", parse_lightspeed_r, "lightspeed-r-products.csv"),
        ("Lightspeed X-Series", parse_lightspeed_x, "lightspeed-x-products.csv"),
        ("Google Merchant Center", parse_google_merchant_center, "google-merchant-center-products.csv"),
    ]

    total_products = 0
    total_variants = 0
    total_skipped = 0
    total_inventory = 0

    for platform_name, parser, csv_file in platforms:
        csv_path = os.path.join(test_dir, csv_file)
        print(f"{'=' * 60}")
        print(f"📦 {platform_name}: {csv_file}")
        print(f"{'=' * 60}")

        try:
            products, skipped = parser(csv_path)
        except Exception as e:
            print(f"  ❌ Parse error: {e}")
            continue

        for s in skipped:
            print(f"  ⏭️  Skipped ({s['reason']}): {s['title']}")
            total_skipped += 1

        for pd in products:
            try:
                result = create_product(store, token, pd["input"])
            except ShopifyAPIError as e:
                print(f"  ❌ API error: {e}")
                total_skipped += 1
                continue

            p = result.get("data", {}).get("productSet", {}).get("product")
            errs = result.get("data", {}).get("productSet", {}).get("userErrors", [])

            if p:
                vc = len(p["variants"]["edges"])
                print(f"  ✅ {p['title']} ({vc} variant{'s' if vc != 1 else ''})")
                total_products += 1
                total_variants += vc

                if location_id:
                    for idx, edge in enumerate(p["variants"]["edges"]):
                        inv_id = edge["node"]["inventoryItem"]["id"]
                        qty = pd["inventory"][idx] if idx < len(pd["inventory"]) else 0
                        if qty > 0:
                            try:
                                set_inventory(store, token, inv_id, location_id, qty)
                                total_inventory += 1
                            except ShopifyAPIError as e:
                                print(f"    ⚠️  Inventory error for {edge['node']['sku']}: {e}")
            else:
                print(f"  ❌ FAILED: {errs[0]['message'] if errs else 'unknown error'}")
                total_skipped += 1

            time.sleep(0.5)

    store_slug = store.replace(".myshopify.com", "")
    print()
    print(f"{'=' * 60}")
    print(f"📊 IMPORT SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Products created:     {total_products}")
    print(f"  Variants created:     {total_variants}")
    print(f"  Products skipped:     {total_skipped}")
    print(f"  Inventory quantities: {total_inventory}")
    print(f"  View products: https://admin.shopify.com/store/{store_slug}/products")


if __name__ == "__main__":
    main()
