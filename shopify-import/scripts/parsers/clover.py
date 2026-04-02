"""Clover item export CSV parser. Single-variant products only."""

from parsers.common import read_csv, safe_float, safe_int

REQUIRED_HEADERS = ["Clover ID", "Name"]


def parse_clover(path):
    rows = read_csv(path)
    products = []
    skipped = []

    for row in rows:
        if row.get("Hidden", "").strip().lower() == "yes":
            skipped.append({"title": row.get("Name", ""), "reason": "hidden item"})
            continue

        price = safe_float(row.get("Price"))
        if row.get("Price Type", "").strip() == "VARIABLE":
            price = 0  # Flag for review

        sv = {"optionValues": [{"optionName": "Title", "name": "Default Title"}],
              "sku": row.get("SKU", ""), "price": price,
              "inventoryItem": {"tracked": True, "requiresShipping": True}}
        barcode = row.get("Product Code", "").strip()
        if barcode:
            sv["barcode"] = barcode
        cost = safe_float(row.get("Cost"))
        if cost:
            sv["inventoryItem"]["cost"] = cost

        tags = [t.strip() for t in row.get("Labels", "").split(",") if t.strip()]
        inp = {
            "title": row["Name"], "productType": row.get("Category", ""),
            "tags": tags, "status": "DRAFT",
            "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
            "variants": [sv],
        }
        products.append({"input": inp, "inventory": [safe_int(row.get("Stock Count"))]})

    return products, skipped
