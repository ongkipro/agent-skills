"""Platform-specific CSV parsers.

Each parser reads a CSV and returns (products, skipped) where:
- products: list of {"input": <productSet input dict>, "inventory": [qty per variant]}
- skipped: list of {"title": str, "reason": str}
"""

from parsers.square import parse_square, REQUIRED_HEADERS as _sq_h
from parsers.woocommerce import parse_woocommerce, REQUIRED_HEADERS as _wc_h
from parsers.etsy import parse_etsy, REQUIRED_HEADERS as _et_h
from parsers.wix import parse_wix, REQUIRED_HEADERS as _wx_h
from parsers.amazon import parse_amazon, REQUIRED_HEADERS as _az_h
from parsers.ebay import parse_ebay, REQUIRED_HEADERS as _eb_h
from parsers.clover import parse_clover, REQUIRED_HEADERS as _cl_h
from parsers.lightspeed_r import parse_lightspeed_r, REQUIRED_HEADERS as _lr_h
from parsers.lightspeed_x import parse_lightspeed_x, REQUIRED_HEADERS as _lx_h
from parsers.google_merchant_center import parse_google_merchant_center, REQUIRED_HEADERS as _gmc_h

PARSERS = {
    "square": parse_square,
    "woocommerce": parse_woocommerce,
    "etsy": parse_etsy,
    "wix": parse_wix,
    "amazon": parse_amazon,
    "ebay": parse_ebay,
    "clover": parse_clover,
    "lightspeed-r": parse_lightspeed_r,
    "lightspeed-x": parse_lightspeed_x,
    "google-merchant-center": parse_google_merchant_center,
}

# Single source of truth for required headers — each parser defines its own.
REQUIRED_HEADERS = {
    "square": _sq_h,
    "woocommerce": _wc_h,
    "etsy": _et_h,
    "wix": _wx_h,
    "amazon": _az_h,
    "ebay": _eb_h,
    "clover": _cl_h,
    "lightspeed-r": _lr_h,
    "lightspeed-x": _lx_h,
    "google-merchant-center": _gmc_h,
}

__all__ = [
    "PARSERS", "REQUIRED_HEADERS",
    "parse_square", "parse_woocommerce", "parse_etsy", "parse_wix",
    "parse_amazon", "parse_ebay", "parse_clover",
    "parse_lightspeed_r", "parse_lightspeed_x", "parse_google_merchant_center",
]
