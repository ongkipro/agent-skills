#!/usr/bin/env python3
"""Tophat edge-case fixtures against a Shopify dev store.

Runs every CSV in test-data/edge-cases/ through its parser and attempts
to create each product via `shopify store execute` (CLI 3.93.0+).

Unlike tophat.py, this script *expects* failures — the goal is to surface
how each parser and the API handle malformed/unusual data.

Prerequisites:
  brew install shopify/shopify/shopify-cli   # needs 3.93.0+
  shopify store auth --store YOUR.myshopify.com \
    --scopes read_products,write_products,read_inventory,write_inventory,read_locations

Usage:
  python3 shopify-import/scripts/testing/tophat_edge_cases.py --store YOUR.myshopify.com
  python3 shopify-import/scripts/testing/tophat_edge_cases.py --dry-run
  python3 shopify-import/scripts/testing/tophat_edge_cases.py --store YOUR.myshopify.com --platform square
  python3 shopify-import/scripts/testing/tophat_edge_cases.py --store YOUR.myshopify.com --report results.json

Expected: a mix of successes, parse errors, API rejections, and skips.
The JSON report captures everything for diffing across parser changes.
"""

import argparse
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from parsers import (
    parse_square, parse_woocommerce, parse_etsy, parse_wix,
    parse_amazon, parse_ebay, parse_clover,
    parse_lightspeed_r, parse_lightspeed_x, parse_google_merchant_center,
)
from shopify_cli import ShopifyCLI, ShopifyCLIError

# Map edge-case CSV filenames to their parser.
EDGE_CASE_MAP = {
    "square-edge-cases.csv": ("Square", parse_square),
    "woocommerce-edge-cases.csv": ("WooCommerce", parse_woocommerce),
    "etsy-edge-cases.csv": ("Etsy", parse_etsy),
    "wix-edge-cases.csv": ("Wix", parse_wix),
    "amazon-edge-cases.csv": ("Amazon", parse_amazon),
    "ebay-edge-cases.csv": ("eBay", parse_ebay),
    "clover-edge-cases.csv": ("Clover", parse_clover),
    "lightspeed-r-edge-cases.csv": ("Lightspeed R", parse_lightspeed_r),
    "lightspeed-x-edge-cases.csv": ("Lightspeed X", parse_lightspeed_x),
    "google-merchant-center-edge-cases.csv": ("Google Merchant Center", parse_google_merchant_center),
    # Structural edge cases — use Square format
    "unicode-heavy.csv": ("Square (unicode)", parse_square),
    "malformed-headers.csv": ("Square (malformed headers)", parse_square),
    "empty-file.csv": ("Square (empty file)", parse_square),
}


def run_platform(platform_name, parser, csv_path, cli, dry_run):
    """Parse one CSV and optionally push to the API. Returns a result dict."""
    result = {
        "platform": platform_name,
        "file": os.path.basename(csv_path),
        "parse_error": None,
        "products": [],
        "skipped": [],
    }

    # --- Parse ---
    try:
        products, skipped = parser(csv_path)
    except Exception as e:
        result["parse_error"] = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc(),
        }
        return result

    result["skipped"] = skipped

    if dry_run:
        for pd in products:
            result["products"].append({
                "title": pd["input"].get("title", "(no title)"),
                "variants": len(pd["input"].get("variants", [])),
                "api_result": "dry-run",
                "api_errors": [],
            })
        return result

    # --- API via shopify store execute ---
    for pd in products:
        title = pd["input"].get("title", "(no title)")
        entry = {
            "title": title,
            "variants": len(pd["input"].get("variants", [])),
            "api_result": None,
            "api_errors": [],
            "inventory_results": [],
        }

        try:
            api_result = cli.create_product(pd["input"])
        except ShopifyCLIError as e:
            entry["api_result"] = "cli_error"
            entry["api_errors"] = [{"message": str(e)}]
            result["products"].append(entry)
            time.sleep(0.5)
            continue

        p = api_result.get("data", {}).get("productSet", {}).get("product")
        user_errors = api_result.get("data", {}).get("productSet", {}).get("userErrors", [])

        if user_errors:
            entry["api_errors"] = [
                {"field": e.get("field"), "message": e["message"], "code": e.get("code")}
                for e in user_errors
            ]

        if p:
            entry["api_result"] = "created"
            entry["product_id"] = p["id"]

            # Set inventory
            for idx, edge in enumerate(p["variants"]["edges"]):
                inv_id = edge["node"]["inventoryItem"]["id"]
                qty = pd["inventory"][idx] if idx < len(pd.get("inventory", [])) else 0
                inv_entry = {"sku": edge["node"].get("sku", ""), "qty": qty, "result": None}
                if qty > 0:
                    try:
                        cli.set_inventory(inv_id, run_platform.location_id, qty)
                        inv_entry["result"] = "set"
                    except ShopifyCLIError as e:
                        inv_entry["result"] = f"error: {e}"
                elif qty < 0:
                    inv_entry["result"] = "skipped_negative"
                else:
                    inv_entry["result"] = "skipped_zero"
                entry["inventory_results"].append(inv_entry)
        else:
            entry["api_result"] = "rejected"

        result["products"].append(entry)
        time.sleep(0.5)

    return result


def print_summary(results):
    """Print a human-readable summary to stdout."""
    total_parsed = 0
    total_created = 0
    total_rejected = 0
    total_parse_errors = 0
    total_skipped = 0

    for r in results:
        print(f"\n{'=' * 60}")
        print(f"📦 {r['platform']}: {r['file']}")
        print(f"{'=' * 60}")

        if r["parse_error"]:
            total_parse_errors += 1
            print(f"  💥 PARSE ERROR: {r['parse_error']['type']}: {r['parse_error']['message']}")
            continue

        for s in r["skipped"]:
            total_skipped += 1
            print(f"  ⏭️  Skipped ({s.get('reason', '?')}): {s.get('title', '?')}")

        for p in r["products"]:
            total_parsed += 1
            status = p["api_result"]
            variants = p["variants"]
            title = p["title"]

            if status == "created":
                total_created += 1
                print(f"  ✅ {title} ({variants} variant{'s' if variants != 1 else ''})")
                if p.get("api_errors"):
                    for e in p["api_errors"]:
                        print(f"     ⚠️  {e['message']}")
                for inv in p.get("inventory_results", []):
                    if "error" in (inv.get("result") or ""):
                        print(f"     ⚠️  Inventory ({inv['sku']}): {inv['result']}")
                    elif inv.get("result") == "skipped_negative":
                        print(f"     ⚠️  Inventory ({inv['sku']}): negative qty skipped")
            elif status == "rejected":
                total_rejected += 1
                errs = "; ".join(e["message"] for e in p.get("api_errors", []))
                print(f"  ❌ REJECTED: {title} — {errs}")
            elif status == "cli_error":
                total_rejected += 1
                errs = "; ".join(e["message"] for e in p.get("api_errors", []))
                print(f"  ❌ CLI ERROR: {title} — {errs[:200]}")
            elif status == "dry-run":
                print(f"  🔍 {title} ({variants} variant{'s' if variants != 1 else ''}) [dry-run]")

    print(f"\n{'=' * 60}")
    print(f"📊 EDGE CASE SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Files processed:      {len(results)}")
    print(f"  Parse errors:         {total_parse_errors}")
    print(f"  Products parsed:      {total_parsed}")
    print(f"  Products created:     {total_created}")
    print(f"  Products rejected:    {total_rejected}")
    print(f"  Products skipped:     {total_skipped}")


def main():
    parser = argparse.ArgumentParser(description="Tophat edge-case fixtures against a dev store")
    parser.add_argument("--store", type=str, help="Store domain (e.g. your-store.myshopify.com)")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, don't call the API")
    parser.add_argument("--platform", type=str, help="Run only one platform (e.g. 'square', 'wix')")
    parser.add_argument("--report", type=str, help="Write JSON report to this file")
    args = parser.parse_args()

    cli = None

    if not args.dry_run:
        if not args.store:
            print("❌ --store is required (or use --dry-run)")
            print("   Example: --store your-store.myshopify.com")
            print()
            print("   First time? Run:")
            print("     shopify store auth --store YOUR.myshopify.com \\")
            print("       --scopes read_products,write_products,read_inventory,write_inventory,read_locations")
            sys.exit(1)

        cli = ShopifyCLI(args.store)
        print(f"🏪 Store: {args.store}")

        location_result = cli.get_location_id()
        if location_result:
            run_platform.location_id, location_name = location_result
            print(f"📍 Location: {location_name} ({run_platform.location_id})")
        else:
            run_platform.location_id = None
            print("⚠️  Could not fetch location. Inventory will be skipped.")

        # Quick auth check
        try:
            cli.execute("{ shop { name } }")
            print("✅ Auth OK")
        except ShopifyCLIError as e:
            print(f"❌ Auth failed: {e}")
            sys.exit(1)
    else:
        print("🔍 Dry-run mode — parsing only, no API calls")

    edge_dir = os.path.join(os.path.dirname(__file__), "..", "..", "test-data", "edge-cases")
    if not os.path.isdir(edge_dir):
        print(f"❌ Edge case directory not found: {edge_dir}")
        sys.exit(1)

    results = []
    for csv_file, (platform_name, parse_fn) in sorted(EDGE_CASE_MAP.items()):
        if args.platform and args.platform.lower() not in platform_name.lower():
            continue

        csv_path = os.path.join(edge_dir, csv_file)
        if not os.path.exists(csv_path):
            print(f"⚠️  Missing fixture: {csv_path}")
            continue

        result = run_platform(platform_name, parse_fn, csv_path, cli, args.dry_run)
        results.append(result)

    print_summary(results)

    if args.report:
        with open(args.report, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 JSON report: {args.report}")

    store_slug = (args.store or "").replace(".myshopify.com", "")
    if store_slug and not args.dry_run:
        print(f"🔗 View products: https://admin.shopify.com/store/{store_slug}/products")


if __name__ == "__main__":
    main()
