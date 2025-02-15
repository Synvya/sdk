"""
AgentStr: Nostr extension for Agno AI agents
"""

from nostr_sdk import ShippingCost, ShippingMethod  # type: ignore

from .merchant import MerchantTools

# Import main classes to make them available at package level
from .models import AgentProfile, MerchantProduct, MerchantStall, NostrProfile

# Import version from pyproject.toml at runtime
try:
    from importlib.metadata import version

    __version__ = version("agentstr")
except Exception:
    __version__ = "unknown"

__all__ = [
    "MerchantTools",
    "MerchantProduct",
    "MerchantStall",
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
    "AgentProfile",
]
