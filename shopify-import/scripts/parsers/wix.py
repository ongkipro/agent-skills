"""Wix CSV parser.

Groups by handleId. fieldType='Product' is the parent, 'Variant' rows are children.
Product options declared via productOptionName1/2/3 on the Product row.
Variant values in columns matching the option names.
Surcharge on variants is added to the base price.
"""

from parsers.common import read_csv, safe_float

REQUIRED_HEADERS = ["handleId", "fieldType", "name"]


def parse_wix(path):
    rows = read_csv(path)
    groups = {}
    order = []  # Preserve insertion order for deterministic output

    for row in rows:
        hid = row.get("handleId", "").strip()
        if not hid:
            continue
        if hid not in groups:
            groups[hid] = {"product": None, "variants": []}
            order.append(hid)
        ft = row.get("fieldType", "").strip()
        if ft == "Product":
            groups[hid]["product"] = row
        elif ft == "Variant":
            groups[hid]["variants"].append(row)

    products = []
    skipped = []

    for hid in order:
        data = groups[hid]
        product_row = data["product"]
        variant_rows = data["variants"]

        if not product_row:
            skipped.append({"title": hid, "reason": "no Product row found"})
            continue

        # Collect option names from the Product row
        option_names = []
        for i in range(1, 4):
            name = product_row.get(f"productOptionName{i}", "").strip()
            if name:
                option_names.append(name)

        if variant_rows and option_names:
            options = []
            for oname in option_names:
                seen = set()
                vals = []
                for v in variant_rows:
                    val = v.get(oname, "").strip()
                    if val and val not in seen:
                        seen.add(val)
                        vals.append(val)
                if vals:
                    options.append({"name": oname, "values": [{"name": v} for v in vals]})

            if not options:
                options = [{"name": "Title", "values": [{"name": "Default Title"}]}]

            variants = []
            inventory = []
            for v in variant_rows:
                opt_values = []
                for oname in option_names:
                    val = v.get(oname, "").strip()
                    if val:
                        opt_values.append({"optionName": oname, "name": val})
                if not opt_values:
                    opt_values = [{"optionName": "Title", "name": "Default Title"}]

                base_price = safe_float(product_row.get("price"))
                surcharge = safe_float(v.get("surcharge"))
                price = base_price + surcharge

                sv = {
                    "optionValues": opt_values,
                    "sku": v.get("sku", ""),
                    "price": price,
                    "inventoryItem": {"tracked": True, "requiresShipping": True},
                }
                weight = safe_float(v.get("weight"))
                if weight:
                    sv["inventoryItem"]["measurement"] = {"weight": {"unit": "KILOGRAMS", "value": weight}}

                variants.append(sv)
                inventory.append(0)

            inp = {
                "title": product_row.get("name", ""),
                "descriptionHtml": product_row.get("description", ""),
                "vendor": product_row.get("brand", ""),
                "handle": hid,
                "status": "DRAFT",
                "productOptions": options,
                "variants": variants,
            }
        else:
            price = safe_float(product_row.get("price"))
            sv = {
                "optionValues": [{"optionName": "Title", "name": "Default Title"}],
                "sku": product_row.get("sku", ""),
                "price": price,
                "inventoryItem": {"tracked": True, "requiresShipping": True},
            }
            weight = safe_float(product_row.get("weight"))
            if weight:
                sv["inventoryItem"]["measurement"] = {"weight": {"unit": "KILOGRAMS", "value": weight}}

            inp = {
                "title": product_row.get("name", ""),
                "descriptionHtml": product_row.get("description", ""),
                "vendor": product_row.get("brand", ""),
                "handle": hid,
                "status": "DRAFT",
                "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
                "variants": [sv],
            }
            inventory = [0]

        tags = []
        collection = product_row.get("collection", "").strip()
        if collection:
            tags.extend([t.strip() for t in collection.split(";") if t.strip()])
        ribbon = product_row.get("ribbon", "").strip()
        if ribbon:
            tags.append(ribbon)
        if tags:
            inp["tags"] = tags

        products.append({"input": inp, "inventory": inventory})

    return products, skipped
