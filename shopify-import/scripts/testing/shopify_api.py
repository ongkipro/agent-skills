"""Shared Shopify Admin GraphQL API client. Used by import.py and tophat.py."""

import json
import os
import urllib.error
import urllib.request

API_VERSION = "2025-01"

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


class ShopifyAPIError(Exception):
    """Raised when a Shopify API call fails."""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class MissingCredentialsError(Exception):
    """Raised when SHOPIFY_STORE or SHOPIFY_ADMIN_TOKEN is not set."""
    pass


def get_credentials():
    """Read store and token from environment. Returns (store, token).

    Raises MissingCredentialsError if either is not set.
    """
    store = os.environ.get("SHOPIFY_STORE")
    token = os.environ.get("SHOPIFY_ADMIN_TOKEN")
    if not store or not token:
        raise MissingCredentialsError(
            "SHOPIFY_STORE and SHOPIFY_ADMIN_TOKEN environment variables are required.\n"
            "  export SHOPIFY_STORE=your-store.myshopify.com\n"
            "  export SHOPIFY_ADMIN_TOKEN=shpat_xxxxxxxxxxxxx"
        )
    return store, token


def graphql(store, token, query, variables=None):
    """Execute a GraphQL query against the Shopify Admin API.

    Raises ShopifyAPIError on HTTP errors (auth failure, rate limiting, etc.).
    """
    url = f"https://{store}/admin/api/{API_VERSION}/graphql.json"
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": token,
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 429:
            raise ShopifyAPIError(f"Rate limited by Shopify API. Wait and retry. Response: {body}", 429)
        elif e.code == 401:
            raise ShopifyAPIError(f"Authentication failed. Check your SHOPIFY_ADMIN_TOKEN. Response: {body}", 401)
        elif e.code == 403:
            raise ShopifyAPIError(f"Access denied. Your app may be missing required scopes. Response: {body}", 403)
        else:
            raise ShopifyAPIError(f"Shopify API returned HTTP {e.code}: {body}", e.code)
    except urllib.error.URLError as e:
        raise ShopifyAPIError(f"Could not connect to {store}: {e.reason}")


def get_location_id(store, token):
    """Fetch the first location ID from the store.

    Returns (location_id, location_name) or None if unavailable.
    Raises ShopifyAPIError on non-403 errors. Returns None silently on 403
    (missing read_locations scope) so callers can skip inventory gracefully.
    """
    try:
        result = graphql(store, token, LOCATIONS_QUERY)
    except ShopifyAPIError as e:
        if e.status_code == 403:
            return None
        raise
    edges = result.get("data", {}).get("locations", {}).get("edges", [])
    if not edges:
        return None
    loc = edges[0]["node"]
    return loc["id"], loc["name"]


def create_product(store, token, input_data):
    """Create or update a product via productSet mutation."""
    return graphql(store, token, PRODUCT_SET_MUTATION, {"input": input_data})


def set_inventory(store, token, inventory_item_id, location_id, quantity):
    """Set inventory quantity for a variant at a location."""
    return graphql(store, token, INVENTORY_SET_MUTATION, {"input": {
        "reason": "correction",
        "name": "available",
        "quantities": [{"inventoryItemId": inventory_item_id, "locationId": location_id, "quantity": quantity}]
    }})
