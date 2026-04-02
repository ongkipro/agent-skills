"""Lightspeed X-Series (Vend) product CSV parser. Groups by handle for variants."""

from parsers.common import read_csv, safe_float, safe_int

REQUIRED_HEADERS = ["id", "name"]


def parse_lightspeed_x(path):
    rows = read_csv(path)
    groups = {}
    order = []

    for row in rows:
        handle = (row.get("handle") or "").strip() or (row.get("name") or "").strip()
        if not handle:
            continue
        if handle not in groups:
            groups[handle] = []
            order.append(handle)
        groups[handle].append(row)

    products = []
    for handle in order:
        variant_rows = groups[handle]
        info = variant_rows[0]

        opt_map = {}
        for i in ["one", "two", "three"]:
            name_col = f"variant_option_{i}_name"
            val_col = f"variant_option_{i}_value"
            name = info.get(name_col, "").strip()
            if name:
                seen = set()
                vals = []
                for r in variant_rows:
                    val = r.get(val_col, "").strip()
                    if val and val not in seen:
                        seen.add(val)
                        vals.append(val)
                if vals:
                    opt_map[name] = {"val_col": val_col, "values": vals}

        options = ([{"name": n, "values": [{"name": v} for v in d["values"]]} for n, d in opt_map.items()]
                   if opt_map else [{"name": "Title", "values": [{"name": "Default Title"}]}])

        variants = []
        inventory = []
        for v in variant_rows:
            if opt_map:
                opt_values = [{"optionName": n, "name": v.get(d["val_col"], "").strip()}
                              for n, d in opt_map.items() if v.get(d["val_col"], "").strip()]
            else:
                opt_values = [{"optionName": "Title", "name": "Default Title"}]

            sv = {"optionValues": opt_values, "sku": v.get("sku", ""),
                  "price": safe_float(v.get("retail_price")),
                  "inventoryItem": {"tracked": True, "requiresShipping": True}}
            cost = safe_float(v.get("supply_price"))
            if cost:
                sv["inventoryItem"]["cost"] = cost
            variants.append(sv)
            inventory.append(safe_int(v.get("current_inventory")))

        tags = [t.strip() for t in info.get("tags", "").split(",") if t.strip()]
        inp = {
            "title": info["name"], "descriptionHtml": info.get("description", ""),
            "productType": info.get("type", ""), "vendor": info.get("brand_name", ""),
            "handle": handle, "tags": tags, "status": "DRAFT",
            "productOptions": options, "variants": variants,
        }
        products.append({"input": inp, "inventory": inventory})

    return products, []
