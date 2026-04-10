"""Lightspeed R-Series product CSV parser. Groups by Item name for variants."""

from parsers.common import read_csv, safe_float, safe_int

REQUIRED_HEADERS = ["System ID", "Item", "Custom SKU"]


def parse_lightspeed_r(path):
    rows = read_csv(path)
    groups = {}
    order = []

    for row in rows:
        name = row["Item"]
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(row)

    products = []
    for name in order:
        variant_rows = groups[name]
        info = variant_rows[0]

        opt_map = {}
        for attr in ["Size", "Color"]:
            seen = set()
            vals = []
            for r in variant_rows:
                val = r.get(attr, "").strip()
                if val and val not in seen:
                    seen.add(val)
                    vals.append(val)
            if vals:
                opt_map[attr] = vals

        # If no Size/Color, each row with different System ID is a separate product.
        # Only group as variants if we actually have option attributes.
        if not opt_map and len(variant_rows) > 1:
            # Split into individual single-variant products
            for v in variant_rows:
                sv = {"optionValues": [{"optionName": "Title", "name": "Default Title"}],
                      "sku": v.get("Custom SKU", ""),
                      "price": safe_float(v.get("Price")),
                      "inventoryItem": {"tracked": True, "requiresShipping": True}}
                barcode = v.get("UPC", "").strip()
                if barcode:
                    sv["barcode"] = barcode
                cost = safe_float(v.get("Default Cost"))
                if cost:
                    sv["inventoryItem"]["cost"] = cost
                inp = {
                    "title": name, "descriptionHtml": v.get("Description", ""),
                    "productType": v.get("Category", ""), "vendor": v.get("Vendor", ""),
                    "status": "DRAFT",
                    "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
                    "variants": [sv],
                }
                products.append({"input": inp, "inventory": [safe_int(v.get("Qty"))]})
            continue

        options = ([{"name": n, "values": [{"name": v} for v in vals]} for n, vals in opt_map.items()]
                   if opt_map else [{"name": "Title", "values": [{"name": "Default Title"}]}])

        variants = []
        inventory = []
        for v in variant_rows:
            if opt_map:
                opt_values = [{"optionName": attr, "name": v.get(attr, "").strip()}
                              for attr in opt_map if v.get(attr, "").strip()]
            else:
                opt_values = [{"optionName": "Title", "name": "Default Title"}]

            sv = {"optionValues": opt_values, "sku": v.get("Custom SKU", ""),
                  "price": safe_float(v.get("Price")),
                  "inventoryItem": {"tracked": True, "requiresShipping": True}}
            barcode = v.get("UPC", "").strip()
            if barcode:
                sv["barcode"] = barcode
            cost = safe_float(v.get("Default Cost"))
            if cost:
                sv["inventoryItem"]["cost"] = cost
            variants.append(sv)
            inventory.append(safe_int(v.get("Qty")))

        inp = {
            "title": name, "descriptionHtml": info.get("Description", ""),
            "productType": info.get("Category", ""), "vendor": info.get("Vendor", ""),
            "status": "DRAFT", "productOptions": options, "variants": variants,
        }
        products.append({"input": inp, "inventory": inventory})

    return products, []
