# Edge Case Test Fixtures for shopify-import

These CSVs exercise the failure modes and edge cases that the happy-path fixtures in `test-data/` don't cover. Each file targets a specific category of real-world messiness.

## Files

| File | What it tests |
|---|---|
| `square-edge-cases.csv` | Empty fields, unicode names, >3 options (Shopify limit), zero-price, duplicate tokens, missing SKUs |
| `woocommerce-edge-cases.csv` | Orphaned variations (parent missing), unpublished products, zero-stock, HTML entities in descriptions, grouped type |
| `etsy-edge-cases.csv` | SKU count mismatch with variant combos, >3 variation types, empty variation values, currency ≠ USD |
| `wix-edge-cases.csv` | Variant row before product row, missing handleId, surcharge with no base price, invisible products |
| `amazon-edge-cases.csv` | Orphaned child (no parent), duplicate parent-sku, empty variation-theme, child with no price |
| `ebay-edge-cases.csv` | Auction+BIN mixed, very long HTML descriptions, pipe-delimited edge cases in variation details, zero quantity |
| `clover-edge-cases.csv` | All VARIABLE pricing, all hidden, empty category, stock count negative |
| `lightspeed-r-edge-cases.csv` | Missing size/color (no variant grouping), duplicate system IDs, zero cost, tax=No |
| `lightspeed-x-edge-cases.csv` | Three variant option columns, empty handle (dedupe by name), negative inventory |
| `google-merchant-center-edge-cases.csv` | Mixed currencies in price field, missing item_group_id on grouped items, out_of_stock, preorder status |
| `malformed-headers.csv` | BOM marker, trailing whitespace in headers, mixed case headers, extra commas |
| `empty-file.csv` | Headers only, no data rows |
| `unicode-heavy.csv` | CJK characters, RTL text, emoji in product names, accented characters in every field |
