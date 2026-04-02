---
name: import-from-etsy
description: Import products from Etsy to Shopify
---

## Export instructions

1. Log in to **Etsy**
2. From Shop Manager, click **Settings → Options**
3. Click the **Download Data** tab
4. In the "Currently for Sale Listings" section, click **Download CSV**
5. Save the file `EtsyListingsDownload.csv`

**Note:** The CSV only includes listings currently for sale. Temporarily relist sold-out items to include them.

## Required CSV headers
`TITLE`, `DESCRIPTION`

## Product column mapping

| Etsy Column | Shopify Field | Notes |
|-------------|---------------|-------|
| TITLE | title | Direct |
| DESCRIPTION | descriptionHtml | Plain text, convert newlines to `<br>` |
| PRICE | price | Lowest price across all variations; applied to all variants |
| CURRENCY_CODE | — | Informational; Shopify uses store currency |
| QUANTITY | — | Sum across variants; cannot be split per-variant |
| TAGS | tags | Comma-separated |
| MATERIALS | tags | Append to tags |
| IMAGE1 through IMAGE10 | images | URLs; import in order |
| VARIATION 1 TYPE | productOptions[0].name | e.g. "Color", "Size" |
| VARIATION 1 NAME | — | Label for the variation (often same as type) |
| VARIATION 1 VALUES | productOptions[0].values | Comma-separated values |
| VARIATION 2 TYPE | productOptions[1].name | Second option |
| VARIATION 2 VALUES | productOptions[1].values | Comma-separated |
| SKU | sku | May contain comma-separated SKUs for variants |

## Variant handling

Etsy exports one row per listing, not per variant. Variants are encoded in VARIATION columns:
- `VARIATION 1 TYPE` = option name (e.g. "Size")
- `VARIATION 1 VALUES` = comma-separated values (e.g. "Small, Medium, Large")
- Generate one Shopify variant per combination of VARIATION 1 × VARIATION 2 values

Since Etsy only exports the **lowest** price and **total** quantity:
- Set all variants to the same price (warn user to adjust)
- Do NOT set inventory quantities (warn user to set manually)

## Known limitations
- **No variant-level pricing** — only lowest price exported. Warn user.
- **No variant-level quantity** — sum only. Skip inventory, warn user.
- **No variant-level SKUs** — if SKU contains commas, attempt to split and assign to variants in order; otherwise use same SKU for all.
- **No customer export** — Etsy does not provide customer CSV export.
- **Images are listing-level** — all variants share the same images.
