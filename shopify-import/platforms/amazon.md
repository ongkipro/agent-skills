---
name: import-from-amazon
description: Import products from Amazon to Shopify
---

## Export instructions

1. Log in to **Amazon Seller Central**
2. Go to **Inventory → Inventory Reports**
3. Select report type: **Active Listings Report** or **All Listings Report**
4. Click **Request Report**
5. Once generated, download the TSV/CSV file

Alternative: Use **Manage All Inventory → Export** for a spreadsheet export.

## Key columns

| Amazon Column | Shopify Field | Notes |
|---------------|---------------|-------|
| item-name | title | Direct |
| item-description | descriptionHtml | May be HTML or plain text |
| seller-sku | sku | Direct |
| price | price | Direct |
| quantity | inventory quantity | Direct |
| asin1 | barcode | ASIN; optionally map to barcode |
| product-id (UPC/EAN) | barcode | Prefer over ASIN if available |
| item-condition | — | Skip if not "New" (used items need manual review) |
| image-url | images | Primary image |
| brand-name | vendor | Direct |
| product-type | productType | Direct |
| parent-child | — | "parent" = product, "child" = variant |
| parent-sku | — | Links child to parent |
| variation-theme | — | Defines which attributes are option names (e.g. "SizeColor") |
| size / color / style | variant option values | Based on variation-theme |

## Variant grouping

Amazon uses parent-child relationships:
- `parent-child = "parent"` → product row
- `parent-child = "child"` → variant row, linked by `parent-sku` matching parent's `seller-sku`
- `variation-theme` tells you which columns are options (e.g. "SizeColor" → Size + Color)
- Products without parent-child → single-variant

## Known limitations
- **ASIN deduplication**: Multiple rows may share an ASIN. Deduplicate by ASIN, keep first.
- **No customer export**: Amazon does not provide customer data export.
- **Used/Refurbished items**: Flag for manual review.
- **Tab-separated values**: Amazon reports are often TSV, not CSV. Parse accordingly.
- **HTML in descriptions**: Amazon descriptions may contain HTML entities; decode them.
