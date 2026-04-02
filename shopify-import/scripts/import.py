#!/usr/bin/env python3
"""Parse and preview a platform CSV import for Shopify.

Parses a platform CSV, validates it, and outputs the productSet mutation
payloads. The agent executes them via `shopify store execute`.

Usage:
  # Preview what will be created:
  python3 import.py products.csv --platform square

  # Output as JSON (for agent / shopify store execute):
  python3 import.py products.csv --platform square --json

  # Skip validation:
  python3 import.py products.csv --platform square --skip-validation

Platform names: square, woocommerce, etsy, wix, amazon, ebay, clover,
                lightspeed-r, lightspeed-x, google-merchant-center

Execution path:
  1. Merchant runs `shopify store auth` to connect their store
  2. Agent runs this script with --json to get mutation payloads
  3. Agent runs `shopify store execute` with each payload

For internal dev/testing, use scripts/testing/tophat.py with direct API access.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from parsers import PARSERS
from validate_csv import validate


def main():
    ap = argparse.ArgumentParser(description="Parse and preview a platform CSV import for Shopify")
    ap.add_argument("csv_path", help="Path to the CSV file")
    ap.add_argument("--platform", required=True, help="Source platform name")
    ap.add_argument("--json", action="store_true", dest="json_output", help="Output mutation payloads as JSON")
    ap.add_argument("--skip-validation", action="store_true", help="Skip pre-import validation")
    args = ap.parse_args()

    if not os.path.exists(args.csv_path):
        print(f"❌ File not found: {args.csv_path}", file=sys.stderr)
        sys.exit(1)

    # --- Validation + Parse ---
    products = None
    skipped = None

    if not args.skip_validation:
        quiet = args.json_output
        if not quiet:
            print(f"🔍 Validating: {args.csv_path} (platform: {args.platform})")

        errors, warnings, stats = validate(args.csv_path, args.platform)

        if not quiet and warnings:
            print(f"  ⚠️  {len(warnings)} warning(s):")
            for w in warnings:
                print(f"    • {w}")

        if errors:
            if quiet:
                json.dump({"errors": errors, "warnings": warnings}, sys.stdout, indent=2)
            else:
                print(f"  ❌ {len(errors)} error(s) — cannot import:")
                for e in errors:
                    print(f"    • {e}")
            sys.exit(1)

        if not quiet:
            print(f"  ✅ Validation passed: {stats['products']} products, {stats['variants']} variants")
            print()

        products = stats["_parsed_products"]
        skipped = stats["skipped"]

    if products is None:
        parser = PARSERS.get(args.platform)
        if parser is None:
            print(f"❌ Unsupported platform: {args.platform}", file=sys.stderr)
            print(f"   Supported: {', '.join(sorted(PARSERS.keys()))}", file=sys.stderr)
            sys.exit(1)
        products, skipped = parser(args.csv_path)

    # --- JSON output (for agents) ---
    if args.json_output:
        output = {
            "products": [{"input": pd["input"], "inventory": pd["inventory"]} for pd in products],
            "skipped": skipped,
            "summary": {
                "products": len(products),
                "variants": sum(len(pd["input"]["variants"]) for pd in products),
                "skipped": len(skipped),
            },
        }
        json.dump(output, sys.stdout, indent=2)
        return

    # --- Human-readable preview ---
    for s in skipped:
        print(f"  ⏭️  Skipped ({s['reason']}): {s['title']}")

    if not products:
        print("  No products to import.")
        sys.exit(0)

    print("📦 Mutations to execute via `shopify store execute`:")
    print()
    for i, pd in enumerate(products):
        inp = pd["input"]
        print(f"  [{i+1}] productSet: {inp['title']}")
        print(f"      Status: {inp['status']}")
        print(f"      Type: {inp.get('productType', '—')}")
        print(f"      Options: {', '.join(o['name'] for o in inp['productOptions'])}")
        print(f"      Variants: {len(inp['variants'])}")
        for v in inp["variants"]:
            opts = " / ".join(ov["name"] for ov in v["optionValues"])
            print(f"        • {opts} — ${v['price']:.2f} (SKU: {v.get('sku', '—')})")
        inv_total = sum(pd["inventory"])
        if inv_total > 0:
            print(f"      Inventory: {inv_total} units total")
        print()

    total_variants = sum(len(pd["input"]["variants"]) for pd in products)
    print(f"Total: {len(products)} products, {total_variants} variants ready to import.")
    print()
    print("To execute: use `shopify store auth` to connect, then `shopify store execute` with each mutation.")
    print("Or run with --json to get machine-readable payloads.")


if __name__ == "__main__":
    main()
