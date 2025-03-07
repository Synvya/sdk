"""
AgentStr: Nostr extension for Agno AI agents
"""

import importlib.metadata
import logging

from agentstr.nostr import NostrClient, generate_keys

from .buyer import BuyerTools
from .merchant import MerchantTools

# Import main classes to make them available at package level
from .models import (
    NostrKeys,
    Product,
    ProductShippingCost,
    Profile,
    Stall,
    StallShippingMethod,
)

# Import version from pyproject.toml at runtime
try:
    __version__ = importlib.metadata.version("agentstr")
except importlib.metadata.PackageNotFoundError:
    logging.warning("Package 'agentstr' not found. Falling back to 'unknown'.")
    __version__ = "unknown"
except ImportError:
    logging.warning("importlib.metadata is not available. Falling back to 'unknown'.")
    __version__ = "unknown"

# Define What is Exposed at the Package Level
__all__ = [
    # Merchant Tools
    "MerchantTools",
    # Buyer Tools
    "BuyerTools",
    # Shipping
    # "ShippingCost",
    # "ShippingMethod",
    # Nostr-related utils
    # "EventId",
    # "Keys",
    # "Kind",
    "NostrClient",
    "generate_keys",
    # "Timestamp",
    # "PublicKey",
    # Models
    "Profile",
    "ProductShippingCost",
    "StallShippingMethod",
    "Product",
    "Stall",
    "NostrKeys",
]

# __all__ = [
#     "NostrClient",
#     "NostrProfile",
#     "AgentProfile",
#     "MerchantProduct",
#     "MerchantStall",
# ]
