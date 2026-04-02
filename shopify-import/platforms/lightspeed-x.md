---
name: import-from-lightspeed-x-series
description: Import products and customers from Lightspeed X-Series (Vend) to Shopify
---

## Export instructions

### Products
1. From Lightspeed X-Series admin, go to **Catalog → Products**
2. Click **Export list**
3. Save as `LightspeedProductDownload.csv`

### Customers
1. Go to **Customers → Customers**
2. Click **Export list**
3. Save as `LightspeedCustomerDownload.csv`

## Required CSV headers (products)
`id`, `name`

## Product column mapping

| Lightspeed X Column | Shopify Field | Notes |
|--------------------|---------------|-------|
| name | title | Direct |
| description | descriptionHtml | Direct |
| sku | sku | Direct |
| id | — | Internal ID |
| handle | handle | URL slug |
| retail_price | price | Direct |
| supply_price | inventoryItem.cost | Direct |
| brand_name | vendor | Direct |
| type | productType | Direct |
| tags | tags | Comma-separated |
| variant_option_one_name | productOptions[0].name | e.g. "Size" |
| variant_option_one_value | option value | Direct |
| variant_option_two_name | productOptions[1].name | e.g. "Color" |
| variant_option_two_value | option value | Direct |
| variant_option_three_name | productOptions[2].name | |
| variant_option_three_value | option value | |
| current_inventory | inventory quantity | Direct |
| image_url | images | Direct |

## Variant handling

Lightspeed X exports one row per variant. Group by `handle` or `name` to collect variants.
Variant option columns are explicit: `variant_option_one_name/value`, `variant_option_two_name/value`, `variant_option_three_name/value`.

## Customer column mapping

| Lightspeed X Column | Shopify Field |
|--------------------|---------------|
| customer_code | — (internal) |
| first_name | firstName |
| last_name | lastName |
| email | email |
| phone | phone |
| company_name | company |
| physical_address_1 | address1 |
| physical_city | city |
| physical_state | province |
| physical_postcode | zip |
| physical_country_id | countryCode |
