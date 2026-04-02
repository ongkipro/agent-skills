---
name: import-from-wix
description: Import products and customers from Wix to Shopify
---

## Export instructions

### Products
1. From your Wix account, go to **Catalog → Store products → Products**
2. Optional: filter products with search
3. Click **More actions → Export**
4. Select All, Filtered, or Selected, then click **Export**
5. Save the CSV

### Customers
1. Go to **Customers & Leads → Contacts**
2. Optional: filter contacts
3. Click **… → Export contacts**
4. Select contacts and export

**Note:** Only the Wix contacts "Regular CSV" format is supported.

## Required CSV headers (products)
`handleId`, `fieldType`, `name`, `sku`

## Product column mapping

| Wix Column | Shopify Field | Notes |
|------------|---------------|-------|
| name | title | Direct |
| description | descriptionHtml | May contain HTML |
| handleId | — | Grouping key: same handleId = same product |
| fieldType | — | "Product" = parent row; "Variant" = variant row |
| sku | sku | Direct |
| price | price | Direct |
| surcharge | — | Add to variant price if present |
| visible | status | "true" → DRAFT (always draft on import) |
| productImageUrl | images | Semicolon-separated URLs |
| collection | tags | Map to tags; Shopify collections created separately |
| ribbon | tags | Badge text, add as tag |
| brand | vendor | Direct |
| weight | weight (kg) | Default unit is kg |
| productOptionName1 | productOptions[0].name | e.g. "Color" |
| productOptionDescription1 | — | Ignored |
| productOptionType1 | — | "DROP_DOWN" or "COLOR" — informational |

## Variant grouping

Wix uses `handleId` to group products and variants:
- Row with `fieldType = "Product"` → product-level data (title, description, images)
- Rows with `fieldType = "Variant"` and same `handleId` → variants

Option values are in the variant rows under columns matching the option names.

## Known limitations
- `surcharge` on variants → add to base price
- Collection mapping → imported as tags, not Shopify collections
- Wix product options beyond 3 → only first 3 imported

## Customer column mapping

| Wix Column | Shopify Field |
|------------|---------------|
| First Name | firstName |
| Last Name | lastName |
| Email | email |
| Phone | phone |
| Company | company |
| Street | address1 |
| City | city |
| Region | province |
| Postal Code | zip |
| Country | countryCode |
