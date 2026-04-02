"""eBay Seller Hub CSV parser.

Skips auction-format listings. Groups variants by Item ID.
Variation Details column: 'Color=Brown|Size=Standard'.
"""

from parsers.common import read_csv, safe_float, safe_int

REQUIRED_HEADERS = ["Title"]


def parse_ebay(path):
    rows = read_csv(path)
    groups = {}
    skipped = []

    for row in rows:
        if row.get("Format", "").strip() == "Auction":
            skipped.append({"title": row.get("Title", ""), "reason": "auction listing"})
            continue
        item_id = (row.get("Item ID") or "").strip() or row.get("Title", "").strip()
        if not item_id:
            skipped.append({"title": "(unknown)", "reason": "missing Item ID and Title"})
            continue
        if item_id not in groups:
            groups[item_id] = []
        groups[item_id].append(row)

    products = []
    for iid, variant_rows in groups.items():
        info = variant_rows[0]

        # Parse variation details: 'Color=Brown|Size=Standard'
        opt_map = {}
        for v in variant_rows:
            vd = v.get("Variation Details", "").strip()
            if vd:
                for pair in vd.split("|"):
                    if "=" in pair:
                        k, val = pair.split("=", 1)
                        k, val = k.strip(), val.strip()
                        if k not in opt_map:
                            opt_map[k] = []
                        if val not in opt_map[k]:
                            opt_map[k].append(val)

        options = ([{"name": n, "values": [{"name": v} for v in vals]} for n, vals in opt_map.items()]
                   if opt_map else [{"name": "Title", "values": [{"name": "Default Title"}]}])

        variants = []
        inventory = []
        for v in variant_rows:
            opt_values = []
            vd = v.get("Variation Details", "").strip()
            if vd and opt_map:
                for pair in vd.split("|"):
                    if "=" in pair:
                        k, val = pair.split("=", 1)
                        opt_values.append({"optionName": k.strip(), "name": val.strip()})
            if not opt_values:
                opt_values = [{"optionName": "Title", "name": "Default Title"}]

            price = safe_float(v.get("Buy It Now price")) or safe_float(v.get("Start price"))
            sv = {"optionValues": opt_values, "sku": v.get("Custom label (SKU)", ""),
                  "price": price, "inventoryItem": {"tracked": True, "requiresShipping": True}}
            variants.append(sv)
            inventory.append(safe_int(v.get("Quantity")))

        inp = {
            "title": info["Title"], "descriptionHtml": info.get("Description", ""),
            "productType": info.get("Category name", ""), "status": "DRAFT",
            "productOptions": options, "variants": variants,
        }
        products.append({"input": inp, "inventory": inventory})

    return products, skipped
