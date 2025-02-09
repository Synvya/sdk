"""
AgentStr: Nostr extension for Phidata AI agents
"""

# Import main classes to make them available at package level
from .marketplace import (
    Profile,
    Merchant,
    MerchantStall,
    MerchantProduct,
    ShippingMethod,
    ShippingCost,
)

# Import version from pyproject.toml at runtime
try:
    from importlib.metadata import version

    __version__ = version("agentstr")
except Exception:
    __version__ = "unknown"

__all__ = [
    "Profile",
    "Merchant",
    "MerchantStall",
    "MerchantProduct",
    "ShippingMethod",
    "ShippingCost",
]
