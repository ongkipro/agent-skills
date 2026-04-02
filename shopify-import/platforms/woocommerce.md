---
name: import-from-woocommerce
description: Import products and customers from WooCommerce to Shopify
---

## Export instructions

### Products
1. From your WooCommerce admin, go to **Products → All Products**
2. Click **Export**
3. Select columns, products, and categories to export
4. Optional: check "Yes, export all custom meta"
5. Click **Generate CSV** and save

### Customers
Requires the **WooCommerce Customer/Order/Coupon Export** plugin or **Import Export Suite**.
1. Go to **Import Export Suite → Export**
2. Select **User/Customer** from dropdown
3. Follow the export wizard and download CSV

## Required CSV headers (products)
`ID`, `Type`, `SKU`, `Name`, `Published`

## Product column mapping

| WooCommerce Column | Shopify Field | Notes |
|-------------------|---------------|-------|
| Name | title | Direct |
| Description | descriptionHtml | May contain HTML |
| Short description | descriptionHtml | Append below main description if present |
| SKU | sku | Direct |
| Regular price | price (or compareAtPrice) | If sale price exists, this becomes compareAtPrice |
| Sale price | price | If present and < regular, this is the selling price |
| Categories | productType (first) + tags (all) | Comma-separated; first becomes productType |
| Tags | tags | Comma-separated, append to any from categories |
| Images | images | Comma-separated URLs |
| Weight (kg) | weight | Parse unit from header; default kg |
| Tax status | taxable | "taxable" → true |
| In stock? | inventoryPolicy | 1 = DENY (stop selling), 0 = CONTINUE |
| Stock | inventory quantity | Integer |
| Backorders allowed? | inventoryPolicy | 1 → CONTINUE |
| Published | status | 1 → DRAFT (we always draft), 0 → DRAFT |
| Type | — | Routing: "simple", "variable", "variation", "grouped", "external" |

## Variant grouping

- `Type = "simple"` → single-variant product
- `Type = "variable"` → parent product row (title, description, images)
- `Type = "variation"` → variant row; `Parent` column links to parent's `ID`
- Attributes: `Attribute 1 name`, `Attribute 1 value(s)` — comma-separated values become option values

## Handling WooCommerce types

| Type | Action |
|------|--------|
| simple | Import as single-variant product |
| variable | Import as parent; collect child "variation" rows as variants |
| variation | Attach to parent via `Parent` column (matches parent `ID`) |
| grouped | Import individual products but warn: grouping not preserved |
| external | Skip — external/affiliate products cannot be imported |

## Known limitations
- Digital/downloadable products → skip, warn user to use Digital Downloads app
- Grouped products → import individually, no grouping in Shopify
- External products → skip entirely
- Custom meta fields → not mapped automatically; warn user

## Customer column mapping

| WooCommerce Column | Shopify Field |
|-------------------|---------------|
| First Name / Billing First Name | firstName |
| Last Name / Billing Last Name | lastName |
| Email | email |
| Billing Phone | phone |
| Billing Company | company |
| Billing Address 1 | address1 |
| Billing Address 2 | address2 |
| Billing City | city |
| Billing State | province |
| Billing Postcode | zip |
| Billing Country | countryCode |
