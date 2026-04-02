---
name: import-from-ebay
description: Import products from eBay to Shopify
---

## Export instructions

1. From eBay's **Seller Hub**, go to **Reports → Downloads**
2. Click **Download Report**
3. Select Source: **Listings**
4. Select Type: **All active listings** or **All unsold listings** (drafts cannot be exported)
5. Click **Download** and save the CSV

## Key columns

| eBay Column | Shopify Field | Notes |
|-------------|---------------|-------|
| Title | title | Truncate to 255 chars; eBay allows up to 80 chars typically |
| Description | descriptionHtml | Often contains heavy HTML; preserve it |
| Custom label (SKU) | sku | Direct |
| Start price | price | For fixed-price listings |
| Buy It Now price | price | Preferred over start price for auctions |
| Quantity | inventory quantity | Direct |
| PicURL | images | Pipe-separated URLs (split on `\|`) |
| Item specifics | tags | Key-value pairs; add as tags |
| Category name | productType | Direct |
| Condition | — | "New" → import; "Used" → flag for review |
| Format | — | "FixedPrice" → import; "Auction" → skip |
| Variation details | variant options | JSON-like or pipe-separated |

## Variant handling

eBay exports can represent variations in two ways:
1. **Separate rows per variation** with a shared parent item ID
2. **Variation details column** with encoded option data

Parse `Variation Details` or group by `Item ID` to build variants.

## Known limitations
- **Auction listings** → skip entirely, not compatible with Shopify
- **Used/Refurbished items** → import but flag for review
- **Product names limited to 15 words** in some eBay exports → Shopify handles longer titles fine
- **Heavy HTML descriptions** → import as-is; merchant may want to clean up
- **No customer export** from eBay
- **Reserve price / start price** → if no Buy It Now, use start price and warn
- **Images**: PicURL may be pipe-delimited; split and import each
