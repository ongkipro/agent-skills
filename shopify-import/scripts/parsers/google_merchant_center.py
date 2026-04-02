"""Google Merchant Center product feed CSV parser.

Groups by item_group_id for variants. Parses prices like '29.99 USD'.
Fix #4: Handles malformed prices gracefully via safe parse functions.
"""

from parsers.common import read_csv, parse_gmc_price, parse_gmc_weight

REQUIRED_HEADERS = ["id", "title"]


def parse_google_merchant_center(path):
    rows = read_csv(path)
    groups = {}
    singles = []

    for row in rows:
        gid = row.get("item_group_id", "").strip()
        if gid:
            if gid not in groups:
                groups[gid] = []
            groups[gid].append(row)
        else:
            singles.append(row)

    products = []

    for gid, variant_rows in groups.items():
        info = variant_rows[0]

        opt_map = {}
        for attr in ["color", "size", "material"]:
            seen = set()
            vals = []
            for r in variant_rows:
                val = r.get(attr, "").strip()
                if val and val not in seen:
                    seen.add(val)
                    vals.append(val)
            if vals:
                opt_map[attr.capitalize()] = vals

        options = ([{"name": n, "values": [{"name": v} for v in vals]} for n, vals in opt_map.items()]
                   if opt_map else [{"name": "Title", "values": [{"name": "Default Title"}]}])

        variants = []
        for r in variant_rows:
            opt_values = [{"optionName": attr.capitalize(), "name": r[attr].strip()}
                          for attr in ["color", "size", "material"]
                          if r.get(attr, "").strip() and attr.capitalize() in opt_map]
            if not opt_values:
                opt_values = [{"optionName": "Title", "name": "Default Title"}]

            reg = parse_gmc_price(r.get("price", ""))
            sale = parse_gmc_price(r.get("sale_price", ""))
            sv = {"optionValues": opt_values, "sku": r.get("id", ""),
                  "price": sale if sale else reg,
                  "inventoryItem": {"tracked": True, "requiresShipping": True}}
            if sale and reg > sale:
                sv["compareAtPrice"] = reg
            barcode = r.get("gtin", "").strip()
            if barcode:
                sv["barcode"] = barcode
            wv, wu = parse_gmc_weight(r.get("shipping_weight", ""))
            if wv:
                sv["inventoryItem"]["measurement"] = {"weight": {"unit": wu, "value": wv}}
            variants.append(sv)

        ptype = info.get("product_type", "").strip()
        if not ptype and info.get("google_product_category"):
            ptype = info["google_product_category"].split(">")[-1].strip()

        tags = [info.get(c, "").strip() for c in ["custom_label_0", "gender", "age_group"] if info.get(c, "").strip()]
        inp = {
            "title": info["title"], "descriptionHtml": info.get("description", "").replace("\n", "<br>"),
            "productType": ptype, "vendor": info.get("brand", ""), "tags": tags,
            "status": "DRAFT", "productOptions": options, "variants": variants,
        }
        products.append({"input": inp, "inventory": [0] * len(variants)})

    for row in singles:
        reg = parse_gmc_price(row.get("price", ""))
        sale = parse_gmc_price(row.get("sale_price", ""))
        sv = {"optionValues": [{"optionName": "Title", "name": "Default Title"}],
              "sku": row.get("id", ""), "price": sale if sale else reg,
              "inventoryItem": {"tracked": True, "requiresShipping": True}}
        if sale and reg > sale:
            sv["compareAtPrice"] = reg
        barcode = row.get("gtin", "").strip()
        if barcode:
            sv["barcode"] = barcode
        wv, wu = parse_gmc_weight(row.get("shipping_weight", ""))
        if wv:
            sv["inventoryItem"]["measurement"] = {"weight": {"unit": wu, "value": wv}}

        ptype = row.get("product_type", "").strip()
        if not ptype and row.get("google_product_category"):
            ptype = row["google_product_category"].split(">")[-1].strip()

        inp = {
            "title": row["title"], "descriptionHtml": row.get("description", "").replace("\n", "<br>"),
            "productType": ptype, "vendor": row.get("brand", ""),
            "status": "DRAFT",
            "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
            "variants": [sv],
        }
        products.append({"input": inp, "inventory": [0]})

    return products, []
