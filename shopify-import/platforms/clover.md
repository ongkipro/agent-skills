---
name: import-from-clover
description: Import products and customers from Clover to Shopify
---

## Export instructions

### Products
1. Log in to **Clover**
2. From your dashboard, click **Items → Item List**
3. Click **⋮** (three dots menu), then click **Export**
4. Save as `CloverItemDownload.csv`

**Note:** Only full item list export is supported. Partial export is not available.

### Customers
1. From dashboard, click **Customers → Customer List**
2. Click **⋮ → Download**
3. Save as `CloverCustomerDownload.csv`

## Required CSV headers (products)
`Clover ID`, `Name`

## Product column mapping

| Clover Column | Shopify Field | Notes |
|---------------|---------------|-------|
| Name | title | Direct |
| Alternate Name | — | Informational; skip or add to description |
| Price | price | In dollars |
| Price Type | — | "FIXED", "PER_UNIT", "VARIABLE" — only FIXED supported |
| Tax Rates | — | Not importable; warn user to configure in Shopify Tax settings |
| Cost | inventoryItem.cost | Direct |
| Product Code (UPC/EAN) | barcode | Direct |
| SKU | sku | Direct |
| Category | productType + tags | Direct |
| Labels | tags | Comma-separated |
| Hidden | status | "Yes" → flag (POS visibility); always import as DRAFT |
| Item Group | — | Clover item groups → not directly mapped |
| Stock Count | inventory quantity | Direct |

## Variant handling

Clover does not have a robust variant system like Shopify. Items with modifier groups should be imported as single products with a note that modifiers need manual setup.

## Known limitations
- **Modifier groups** → not importable; warn user to use Shopify variant options or apps
- **Variable pricing** (Price Type = "VARIABLE") → set price to 0, warn user
- **Per-unit pricing** → not supported in Shopify; set to base price, warn
- **Tax rates** → Shopify uses its own tax system; skip, advise manual config
- **Hidden items** → import as DRAFT, note POS visibility must be set separately
- **Decimal quantities** → not supported by Shopify; round to nearest integer

## Customer column mapping

| Clover Column | Shopify Field |
|---------------|---------------|
| First Name | firstName |
| Last Name | lastName |
| Email | email |
| Phone | phone |
| Address Line 1 | address1 |
| Address Line 2 | address2 |
| City | city |
| State | province |
| Zip | zip |
| Note | note |
