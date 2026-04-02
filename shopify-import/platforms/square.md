---
name: import-from-square
description: Import products and customers from Square to Shopify
---

## Export instructions

### Products
1. In your Square account, go to **Items & orders → Items**
2. Click **Actions → Export Library**
3. Select **Export to CSV** and click Export
4. Save the file (usually named `items-YYYY-MM-DD.csv`)

### Customers
1. Go to **Customers → Customers → Directory**
2. Click **Import / Export → Export Customers**
3. Select **All Customers** or **Specific Groups**, click Export
4. Click **Download** and save

## Required CSV headers (products)
`Token`, `Item Name`, `Variation Name`, `Description`, `SKU`

## Product column mapping

| Square Column | Shopify Field | Notes |
|---------------|---------------|-------|
| Token | — | Grouping key. Same Token = same product, different variants |
| Item Name | title | Direct |
| Variation Name | variant option value | Used as the variant's option value |
| Description | descriptionHtml | May contain HTML |
| SKU | sku | Direct |
| Category | productType + tags | Direct |
| SEO Title | seo.title | Truncate to 70 chars |
| SEO Description | seo.description | Truncate to 320 chars |
| Permalink | handle | Direct |
| GTIN | barcode | Direct |
| Price | price | Already in dollars |
| Online Sale Price | compareAtPrice / price | If sale price exists and < regular price, set price=sale, compareAtPrice=regular |
| Weight (kg) / Weight (lb) | weight + unit | Parse unit from column header |
| Default Unit Cost | inventoryItem.cost | Direct |
| Option Name 1-3 | productOptions[].name | Direct |
| Option Value 1-3 | variant optionValues | Direct |
| Enabled {location} | — | Y/N, used with quantity |
| Current Quantity {location} | inventory quantity | Integer; only for enabled locations |
| Archived | — | If Y, skip this product entirely |

## Variant grouping

Rows sharing the same `Token` are variants of one product. The first row's `Item Name`, `Description`, `Category`, `SEO Title`, `SEO Description`, and `Permalink` define the product. Each row contributes one variant.

## Single-variant products

If a product has no Option Name/Value columns filled, use `"Title"` as the option name and the `Variation Name` as the value.

## Known limitations
- `Archived = Y` → skip entirely
- `Unit and Precision` (price-per-unit) → not supported, skip and warn
- Prices by location → not supported, use base `Price` only
- > 3 option types → only first 3 imported, warn user
- Modifier Sets → not supported, warn user

## Customer column mapping

| Square Column | Shopify Field |
|---------------|---------------|
| First Name | firstName |
| Surname | lastName |
| Email Address | email |
| Phone Number | phone |
| Company Name | company |
| Address Line 1 | address1 |
| Address Line 2 | address2 |
| City / Locality | city |
| State / Province | province |
| Zip / Postal Code | zip |
| Country | countryCode (resolve to ISO) |
| Email Subscription Status | emailMarketingConsent ("Subscribed" → SUBSCRIBED) |
