"""
AgentStr: Nostr extension for Agno AI agents
"""

import importlib.metadata
import logging

from nostr_sdk import ShippingCost, ShippingMethod, Timestamp  # type: ignore

from agentstr.nostr import EventId, Keys, Kind, NostrClient, generate_and_save_keys

from .buyer import BuyerTools
from .merchant import MerchantTools

# Import main classes to make them available at package level
from .models import AgentProfile, MerchantProduct, MerchantStall, NostrProfile

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
    "MerchantProduct",
    "MerchantStall",
    # Buyer Tools
    "BuyerTools",
    # Shipping
    "ShippingCost",
    "ShippingMethod",
    # Nostr-related utils
    "EventId",
    "Keys",
    "Kind",
    "NostrClient",
    "generate_and_save_keys",
    "Timestamp",
    # Models
    "AgentProfile",
    "NostrProfile",
]
