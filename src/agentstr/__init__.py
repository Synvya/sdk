"""
AgentStr: Nostr extension for Phidata AI agents
"""

from nostr_sdk import ShippingCost, ShippingMethod  # type: ignore

# Import main classes to make them available at package level
from .merchant import Merchant, MerchantProduct, MerchantStall, Profile

# Import version from pyproject.toml at runtime
try:
    from importlib.metadata import version

    __version__ = version("agentstr")
except Exception:
    __version__ = "unknown"

__all__ = [
    "Merchant",
    "MerchantProduct",
    "MerchantStall",
    "Profile",
    "ShippingCost",
    "ShippingMethod",
]

from agentstr.nostr import EventId, Keys, NostrClient, ProductData, StallData

__all__ = [
    "EventId",
    "Keys",
    "NostrClient",
    "ProductData",
    "StallData",
]
