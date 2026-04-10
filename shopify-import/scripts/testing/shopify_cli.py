"""Shopify CLI wrapper — executes GraphQL via `shopify store execute`.

No API tokens needed. Uses OAuth via `shopify store auth`.

Prerequisites:
  - Shopify CLI 3.93.0+ (`brew install shopify/shopify/shopify-cli`)
  - Run `shopify store auth --store your-store.myshopify.com --scopes read_products,write_products,read_inventory,write_inventory,read_locations`

Usage:
  from shopify_cli import ShopifyCLI

  cli = ShopifyCLI(store="your-store.myshopify.com")
  result = cli.execute(query, variables)
"""

import json
import subprocess


class ShopifyCLIError(Exception):
    """Raised when a CLI execution fails."""
    pass


class ShopifyCLI:
    """Wraps `shopify store execute` for GraphQL operations."""

    PRODUCT_SET_MUTATION = """mutation productSet($input: ProductSetInput!) {
        productSet(input: $input) {
            product {
                id title handle status
                variants(first: 100) {
                    edges { node { id title sku price inventoryItem { id } } }
                }
            }
            userErrors { field message code }
        }
    }"""

    INVENTORY_SET_MUTATION = """mutation inventorySetQuantities($input: InventorySetQuantitiesInput!) {
        inventorySetQuantities(input: $input) {
            inventoryAdjustmentGroup { reason }
            userErrors { field message }
        }
    }"""

    LOCATIONS_QUERY = "{ locations(first: 1) { edges { node { id name } } } }"

    # Pin to 2025-01 for inventory mutations — latest version requires
    # changeFromQuantity on both Set and Adjust, which we don't have.
    API_VERSION = "2025-04"

    def __init__(self, store):
        self.store = store

    def execute(self, query, variables=None, allow_mutations=False):
        """Run a GraphQL query/mutation via `shopify store execute`.

        Returns parsed JSON response.
        Raises ShopifyCLIError on failure.
        """
        cmd = [
            "shopify", "store", "execute",
            "--store", self.store,
            "--query", query,
            "--json",
        ]

        if variables:
            cmd.extend(["--variables", json.dumps(variables)])

        if allow_mutations:
            cmd.append("--allow-mutations")

        cmd.extend(["--version", self.API_VERSION])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except FileNotFoundError:
            raise ShopifyCLIError(
                "Shopify CLI not found. Install: brew install shopify/shopify/shopify-cli\n"
                "Requires version 3.93.0+"
            )
        except subprocess.TimeoutExpired:
            raise ShopifyCLIError("Shopify CLI timed out after 60s")

        if result.returncode != 0:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            # Common errors
            if "No stored auth" in stderr or "Run `shopify store auth`" in stderr:
                raise ShopifyCLIError(
                    f"No auth for {self.store}. Run:\n"
                    f"  shopify store auth --store {self.store} "
                    f"--scopes read_products,write_products,read_inventory,write_inventory,read_locations"
                )
            raise ShopifyCLIError(
                f"CLI exited with code {result.returncode}\n"
                f"stderr: {stderr}\n"
                f"stdout: {stdout}"
            )

        stdout = result.stdout.strip()
        if not stdout:
            raise ShopifyCLIError("CLI returned empty output")

        # --json flag should give us clean JSON, but find it just in case
        json_start = stdout.find("{")
        if json_start == -1:
            raise ShopifyCLIError(f"No JSON in CLI output: {stdout[:500]}")

        try:
            return json.loads(stdout[json_start:])
        except json.JSONDecodeError as e:
            raise ShopifyCLIError(f"Failed to parse CLI JSON: {e}\nOutput: {stdout[:500]}")

    def create_product(self, input_data):
        """Create a product via productSet mutation.

        Returns result in the same shape as the direct API: {"data": {"productSet": ...}}
        The CLI strips the outer "data" wrapper, so we re-add it for compatibility.
        """
        result = self.execute(self.PRODUCT_SET_MUTATION, {"input": input_data}, allow_mutations=True)
        if "data" not in result and "productSet" in result:
            result = {"data": result}
        return result

    def set_inventory(self, inventory_item_id, location_id, quantity):
        """Set inventory quantity for a variant at a location."""
        result = self.execute(self.INVENTORY_SET_MUTATION, {"input": {
            "reason": "correction",
            "name": "available",
            "ignoreCompareQuantity": True,
            "quantities": [{
                "inventoryItemId": inventory_item_id,
                "locationId": location_id,
                "quantity": quantity,
            }],
        }}, allow_mutations=True)
        if "data" not in result and "inventorySetQuantities" in result:
            result = {"data": result}
        return result

    def get_location_id(self):
        """Fetch the first location. Returns (id, name) or None."""
        try:
            result = self.execute(self.LOCATIONS_QUERY)
        except ShopifyCLIError:
            return None
        # CLI strips "data" wrapper
        data = result.get("data", result)
        edges = data.get("locations", {}).get("edges", [])
        if not edges:
            return None
        loc = edges[0]["node"]
        return loc["id"], loc["name"]
