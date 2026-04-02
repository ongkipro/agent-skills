"""Etsy CSV parser.

One row per listing. Variants encoded in VARIATION 1/2 TYPE + VALUES columns.
Etsy only exports lowest price and total quantity — cannot split per variant.
Fix #9: Warns when SKU count doesn't match variant combination count.
"""

from itertools import product as iterproduct
from parsers.common import read_csv, safe_float

REQUIRED_HEADERS = ["TITLE", "DESCRIPTION"]


def parse_etsy(path):
    rows = read_csv(path)
    products = []
    skipped = []

    for row in rows:
        title = row["TITLE"]
        desc = row["DESCRIPTION"].replace("\n", "<br>")
        price = safe_float(row.get("PRICE"))
        tags = [t.strip() for t in (row.get("TAGS", "") + "," + row.get("MATERIALS", "")).split(",") if t.strip()]

        # Parse variations
        options = []
        var_values_list = []
        for i in range(1, 3):
            vtype = row.get(f"VARIATION {i} TYPE", "").strip()
            vvals = row.get(f"VARIATION {i} VALUES", "").strip()
            if vtype and vvals:
                vals = [v.strip() for v in vvals.split(",") if v.strip()]
                options.append({"name": vtype, "values": [{"name": v} for v in vals]})
                var_values_list.append([(vtype, v) for v in vals])

        if not options:
            options = [{"name": "Title", "values": [{"name": "Default Title"}]}]
            variants = [{"optionValues": [{"optionName": "Title", "name": "Default Title"}],
                         "sku": row.get("SKU", ""), "price": price}]
        else:
            combos = list(iterproduct(*var_values_list))
            skus = [s.strip() for s in row.get("SKU", "").split(",") if s.strip()]
            variants = []

            # Fix #9: Track SKU mismatch
            if skus and len(skus) != len(combos):
                skipped.append({
                    "title": title,
                    "reason": f"SKU count ({len(skus)}) doesn't match variant count ({len(combos)}) — SKUs assigned in order, remainder gets first SKU"
                })

            for idx, combo in enumerate(combos):
                sv = {
                    "optionValues": [{"optionName": name, "name": val} for name, val in combo],
                    "price": price,
                    "sku": skus[idx] if idx < len(skus) else (skus[0] if skus else ""),
                }
                variants.append(sv)

        inp = {
            "title": title,
            "descriptionHtml": desc,
            "tags": tags,
            "status": "DRAFT",
            "productOptions": options,
            "variants": variants,
        }
        products.append({"input": inp, "inventory": [0] * len(variants)})

    return products, skipped
