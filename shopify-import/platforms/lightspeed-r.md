---
name: import-from-lightspeed-r-series
description: Import products and customers from Lightspeed Retail (R-Series) to Shopify
---

## Export instructions

### Products
1. From Lightspeed R-Series admin, go to **Inventory → Item Search**
2. Optional: filter with search (only filtered items are exported)
3. Click **Export**
4. Save as `LightspeedProductDownload.csv`

### Customers
1. Go to **Customers → Customers**
2. Optional: filter with search
3. Click **Export**
4. Save as `LightspeedCustomerDownload.csv`

## Required CSV headers (products)
`System ID`, `Category`, `Item`, `Custom SKU`, `Price`, `Tax`, `Vendor`, `UPC`

## Product column mapping

| Lightspeed R Column | Shopify Field | Notes |
|--------------------|---------------|-------|
| Item | title | Direct |
| Description | descriptionHtml | Direct |
| Custom SKU | sku | Direct |
| System ID | — | Internal ID; used for deduplication |
| UPC | barcode | Direct |
| Price | price | Direct |
| Default Cost | inventoryItem.cost | Direct |
| Category | productType | Direct |
| Vendor / Manufacturer | vendor | Direct |
| Tax | taxable | "Yes" → true |
| Qty | inventory quantity | Direct |
| Reorder Point | — | Not mapped |
| Reorder Level | — | Not mapped |

## Variant handling

Lightspeed R-Series uses a matrix system. Variants may appear as separate rows with the same base `Item` name but different attribute values. Group by `Item` name and extract option values from columns like `Size`, `Color`, or attribute columns.

## Customer column mapping

| Lightspeed R Column | Shopify Field |
|--------------------|---------------|
| Customer ID | — (internal) |
| First Name | firstName |
| Last Name | lastName |
| Email | email |
| Phone | phone |
| Company | company |
| Address1 | address1 |
| Address2 | address2 |
| City | city |
| State | province |
| Zip | zip |
| Country | countryCode |
