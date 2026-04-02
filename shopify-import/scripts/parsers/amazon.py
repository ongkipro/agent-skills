"""Amazon Seller Central CSV parser.

Parent-child relationships: parent-child='parent' is the product, 'child' rows are variants.
Fix #3: Child rows with unknown parent are skipped with warning, not silently added as singles.
"""

from parsers.common import read_csv, safe_float, safe_int

REQUIRED_HEADERS = ["item-name", "seller-sku"]


def parse_amazon(path):
    rows = read_csv(path)
    parents = {}
    singles = []
    skipped = []

    for row in rows:
        pc = row.get("parent-child", "").strip().lower()
        if pc == "parent":
            parents[row["seller-sku"]] = {"info": row, "children": []}
        elif pc == "child":
            psku = row.get("parent-sku", "").strip()
            if psku in parents:
                parents[psku]["children"].append(row)
            else:
                # Fix #3: Report orphaned children instead of silently treating as singles
                skipped.append({
                    "title": row.get("item-name", f"Child SKU: {row.get('seller-sku', '?')}"),
                    "reason": f"orphaned variant — parent SKU '{psku}' not found"
                })
        else:
            singles.append(row)

    products = []

    for psku, data in parents.items():
        info = data["info"]
        children = data["children"]
        if not children:
            continue

        opt_map = {}
        for attr in ["color", "size"]:
            seen = set()
            vals = []
            for r in children:
                val = r.get(attr, "").strip()
                if val and val not in seen:
                    seen.add(val)
                    vals.append(val)
            if vals:
                opt_map[attr.capitalize()] = vals

        options = [{"name": n, "values": [{"name": v} for v in vals]} for n, vals in opt_map.items()]
        if not options:
            options = [{"name": "Title", "values": [{"name": "Default Title"}]}]

        variants = []
        inventory = []
        for r in children:
            opt_values = []
            for attr in ["color", "size"]:
                val = r.get(attr, "").strip()
                if val and attr.capitalize() in opt_map:
                    opt_values.append({"optionName": attr.capitalize(), "name": val})
            if not opt_values:
                opt_values = [{"optionName": "Title", "name": "Default Title"}]

            sv = {"optionValues": opt_values, "sku": r.get("seller-sku", ""),
                  "price": safe_float(r.get("price")),
                  "inventoryItem": {"tracked": True, "requiresShipping": True}}
            barcode = r.get("product-id", "").strip()
            if barcode:
                sv["barcode"] = barcode
            variants.append(sv)
            inventory.append(safe_int(r.get("quantity")))

        inp = {
            "title": info.get("item-name") or children[0].get("item-name", ""),
            "descriptionHtml": info.get("item-description") or children[0].get("item-description", ""),
            "vendor": info.get("brand-name") or children[0].get("brand-name", ""),
            "productType": info.get("product-type") or children[0].get("product-type", ""),
            "status": "DRAFT",
            "productOptions": options,
            "variants": variants,
        }
        products.append({"input": inp, "inventory": inventory})

    for row in singles:
        sv = {"optionValues": [{"optionName": "Title", "name": "Default Title"}],
              "sku": row.get("seller-sku", ""), "price": safe_float(row.get("price")),
              "inventoryItem": {"tracked": True, "requiresShipping": True}}
        barcode = row.get("product-id", "").strip()
        if barcode:
            sv["barcode"] = barcode
        inp = {
            "title": row["item-name"], "descriptionHtml": row.get("item-description", ""),
            "vendor": row.get("brand-name", ""), "productType": row.get("product-type", ""),
            "status": "DRAFT",
            "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
            "variants": [sv],
        }
        products.append({"input": inp, "inventory": [safe_int(row.get("quantity"))]})

    return products, skipped
