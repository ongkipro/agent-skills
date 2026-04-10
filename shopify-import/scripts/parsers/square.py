"""Square CSV parser.

Grouping: rows with same 'Token' are variants of one product.
Skips: Archived=Y, Unit and Precision (per-unit pricing).
"""

from parsers.common import read_csv, safe_float, safe_int, parse_weight_column

REQUIRED_HEADERS = ["Token", "Item Name", "Variation Name", "Description", "SKU"]


def parse_square(path):
    rows = read_csv(path)
    groups = {}
    skipped = []

    for row in rows:
        if row.get("Archived", "").upper() == "Y":
            skipped.append({"title": row.get("Item Name", ""), "reason": "archived"})
            continue
        if row.get("Unit and Precision", "").strip():
            skipped.append({"title": row.get("Item Name", ""), "reason": "per-unit pricing not supported"})
            continue
        token = row["Token"]
        if token not in groups:
            groups[token] = []
        groups[token].append(row)

    products = []
    for token, variant_rows in groups.items():
        info = variant_rows[0]

        # Collect options from Option Name/Value columns
        option_names = []
        options = []
        for i in range(1, 4):
            name = (info.get(f"Option Name {i}") or "").strip()
            if name:
                option_names.append(name)
                seen = set()
                vals = []
                for v in variant_rows:
                    val = (v.get(f"Option Value {i}") or "").strip()
                    if val and val not in seen:
                        seen.add(val)
                        vals.append(val)
                options.append({"name": name, "values": [{"name": v} for v in vals]})

        if not options:
            option_names = ["Title"]
            vname = info.get("Variation Name", "Default Title").strip()
            options = [{"name": "Title", "values": [{"name": vname}]}]

        variants = []
        inventory = []
        for v in variant_rows:
            if option_names == ["Title"]:
                opt_values = [{"optionName": "Title", "name": (v.get("Variation Name") or "Default Title").strip()}]
            else:
                opt_values = []
                for i, name in enumerate(option_names):
                    val = (v.get(f"Option Value {i+1}") or "").strip()
                    if val:
                        opt_values.append({"optionName": name, "name": val})

            regular_price = safe_float(v.get("Price"))
            sale_price_str = (v.get("Online Sale Price") or "").strip()
            sv = {"optionValues": opt_values, "sku": v.get("SKU", ""), "price": regular_price}

            # Fix #1: Only set compareAtPrice if sale < regular
            if sale_price_str:
                sale_price = safe_float(sale_price_str)
                if 0 < sale_price < regular_price:
                    sv["compareAtPrice"] = regular_price
                    sv["price"] = sale_price

            gtin = v.get("GTIN", "").strip()
            if gtin:
                sv["barcode"] = gtin

            inv_item = {"requiresShipping": True, "tracked": True}
            for col in v:
                if col and col.startswith("Weight"):
                    wv, wu = parse_weight_column(col, v[col])
                    if wv is not None:
                        inv_item["measurement"] = {"weight": {"unit": wu, "value": wv}}

            cost = (v.get("Default Unit Cost") or "").strip()
            if cost:
                inv_item["cost"] = safe_float(cost)
            sv["inventoryItem"] = inv_item

            qty = 0
            for col in v:
                if col and col.startswith("Current Quantity"):
                    enabled_col = col.replace("Current Quantity", "Enabled")
                    if v.get(enabled_col, "").upper() == "Y":
                        qty += safe_int(v[col])
            inventory.append(qty)
            variants.append(sv)

        inp = {
            "title": info["Item Name"],
            "descriptionHtml": info.get("Description", ""),
            "handle": info.get("Permalink", ""),
            "productType": info.get("Category", ""),
            "status": "DRAFT",
            "productOptions": options,
            "variants": variants,
        }
        seo_title = info.get("SEO Title", "").strip()
        seo_desc = info.get("SEO Description", "").strip()
        if seo_title or seo_desc:
            inp["seo"] = {}
            if seo_title:
                inp["seo"]["title"] = seo_title[:70]
            if seo_desc:
                inp["seo"]["description"] = seo_desc[:320]

        products.append({"input": inp, "inventory": inventory})

    return products, skipped
