"""WooCommerce CSV parser.

Types: simple (single product), variable+variation (parent/child), external (skip).
Fix #2: Orphaned variations (parent ID not found) are reported as skipped.
"""

from parsers.common import read_csv, safe_float, safe_int

REQUIRED_HEADERS = ["ID", "Type", "SKU", "Name", "Published"]


def _woo_price(row):
    """Extract price and compareAtPrice from a WooCommerce row.

    If sale price exists and is less than regular, price=sale and compareAtPrice=regular.
    """
    sale = safe_float(row.get("Sale price"))
    regular = safe_float(row.get("Regular price"))
    if sale and regular and sale < regular:
        return sale, regular
    return regular or sale, None


def parse_woocommerce(path):
    rows = read_csv(path)
    parents = {}
    simples = []
    skipped = []

    for row in rows:
        t = row.get("Type", "").strip().lower()
        if t == "external":
            skipped.append({"title": row.get("Name", ""), "reason": "external/affiliate product"})
            continue
        if t == "variable":
            parents[row["ID"]] = {"info": row, "children": []}
        elif t == "variation":
            pid = row.get("Parent", "").replace("id:", "")
            if pid in parents:
                parents[pid]["children"].append(row)
            else:
                # Fix #2: Report orphaned variations instead of silently dropping
                skipped.append({"title": row.get("Name", f"Variation (parent ID: {pid})"),
                                "reason": "orphaned variation — parent product not found"})
        elif t == "simple":
            simples.append(row)

    products = []

    for row in simples:
        price, compare = _woo_price(row)
        sv = {
            "optionValues": [{"optionName": "Title", "name": "Default Title"}],
            "sku": row.get("SKU", ""),
            "price": price,
            "inventoryItem": {"tracked": True, "requiresShipping": True},
        }
        if compare:
            sv["compareAtPrice"] = compare
        weight = safe_float(row.get("Weight (kg)"))
        if weight:
            sv["inventoryItem"]["measurement"] = {"weight": {"unit": "KILOGRAMS", "value": weight}}

        inp = {
            "title": row["Name"],
            "descriptionHtml": row.get("Description", "") or row.get("Short description", ""),
            "productType": (row.get("Categories", "").split(",")[0].strip() if row.get("Categories") else ""),
            "tags": [t.strip() for t in row.get("Tags", "").split(",") if t.strip()],
            "status": "DRAFT",
            "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
            "variants": [sv],
        }
        products.append({"input": inp, "inventory": [safe_int(row.get("Stock"))]})

    for pid, data in parents.items():
        info = data["info"]
        children = data["children"]
        if not children:
            continue

        opt_map = {}
        for v in children:
            for i in range(1, 4):
                name = v.get(f"Attribute {i} name", "").strip()
                val = v.get(f"Attribute {i} value(s)", "").strip()
                if name and val:
                    if name not in opt_map:
                        opt_map[name] = []
                    for vv in val.split(","):
                        vv = vv.strip()
                        if vv and vv not in opt_map[name]:
                            opt_map[name].append(vv)

        options = [{"name": n, "values": [{"name": v} for v in vals]} for n, vals in opt_map.items()]
        variants = []
        inventory = []

        for v in children:
            opt_values = []
            for i in range(1, 4):
                name = v.get(f"Attribute {i} name", "").strip()
                val = v.get(f"Attribute {i} value(s)", "").strip()
                if name and val:
                    opt_values.append({"optionName": name, "name": val})

            price, compare = _woo_price(v)
            sv = {"optionValues": opt_values, "sku": v.get("SKU", ""), "price": price,
                  "inventoryItem": {"tracked": True, "requiresShipping": True}}
            if compare:
                sv["compareAtPrice"] = compare
            weight = safe_float(v.get("Weight (kg)"))
            if weight:
                sv["inventoryItem"]["measurement"] = {"weight": {"unit": "KILOGRAMS", "value": weight}}
            variants.append(sv)
            inventory.append(safe_int(v.get("Stock")))

        inp = {
            "title": info["Name"],
            "descriptionHtml": info.get("Description", "") or info.get("Short description", ""),
            "productType": (info.get("Categories", "").split(",")[0].strip() if info.get("Categories") else ""),
            "tags": [t.strip() for t in info.get("Tags", "").split(",") if t.strip()],
            "status": "DRAFT",
            "productOptions": options,
            "variants": variants,
        }
        products.append({"input": inp, "inventory": inventory})

    return products, skipped
