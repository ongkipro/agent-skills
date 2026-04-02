---
name: import-from-google-merchant-center
description: Import products from Google Merchant Center to Shopify
---

## Export instructions

1. Log in to **Google Merchant Center** at merchantcenter.google.com
2. Go to **Products → All products**
3. Click the **download icon** (↓) or go to **Products → Feeds**
4. Select your primary feed and click **Download**
5. Save the file (TSV or CSV format)

Alternative: Go to **Products → Feeds → your feed → Download file**

## Key columns (Google Product Data Specification)

| GMC Column | Shopify Field | Notes |
|------------|---------------|-------|
| title | title | Direct |
| description | descriptionHtml | Plain text; convert newlines to `<br>` |
| id | sku | Merchant's internal ID; use as SKU |
| link | — | URL to product on merchant's existing site |
| image_link | images[0] | Primary image URL |
| additional_image_link | images[1+] | Comma-separated additional image URLs |
| price | price | Format: "29.99 USD" — parse number, ignore currency |
| sale_price | price / compareAtPrice | If present: price = sale_price, compareAtPrice = price |
| availability | — | "in_stock" → tracked=true; "out_of_stock" → quantity=0 |
| brand | vendor | Direct |
| gtin | barcode | EAN/UPC/ISBN |
| mpn | sku (fallback) | Manufacturer part number; use as SKU if `id` not suitable |
| google_product_category | productType | Google taxonomy string; use last segment |
| product_type | productType | Merchant's own category; prefer over google_product_category |
| item_group_id | — | Grouping key: same item_group_id = same product, different variants |
| color | option: Color | Variant option |
| size | option: Size | Variant option |
| material | option: Material | Variant option |
| pattern | tags | Add as tag |
| gender | tags | Add as tag |
| age_group | tags | Add as tag |
| condition | — | "new" → import; "used"/"refurbished" → flag |
| shipping_weight | weight | Format: "0.5 kg" — parse value and unit |
| custom_label_0-4 | tags | Merchant's custom labels; add as tags |

## Variant grouping

GMC uses `item_group_id` to link variants:
- All rows with the same `item_group_id` are variants of one product
- The product title, description, and category come from any row (they should be identical across variants)
- Each row's `color`, `size`, `material` values become variant options
- Rows without `item_group_id` are standalone single-variant products

## Price parsing

GMC prices include currency: `"29.99 USD"`, `"€24.50"`, `"1299 JPY"`
- Extract numeric value only
- Shopify uses the store's currency; warn if GMC currency differs

## Image handling

- `image_link` = primary image (required)
- `additional_image_link` = comma-separated additional images
- All must be publicly accessible HTTPS URLs
- GMC images are typically high-quality and ready to use

## Known limitations
- **Currency mismatch**: GMC feed may be in different currency than Shopify store. Warn user.
- **Google taxonomy**: `google_product_category` is a long path like "Apparel & Accessories > Shoes > Athletic Shoes". Use the last segment as productType.
- **No customer data**: GMC is product feeds only.
- **No inventory quantities**: GMC has `availability` (in_stock/out_of_stock) but not exact quantities. Set tracked=true, warn user to set quantities manually.
- **TSV format**: Google feeds are often tab-separated. Parse accordingly.
- **Encoded HTML entities**: Descriptions may have `&amp;`, `&lt;`, etc. Decode them.
