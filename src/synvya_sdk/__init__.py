"""
Synvya SDK: Tools for a Nostr agentic ecosystem
"""

import importlib.metadata
import logging

# Import main classes to make them available at package level
from .models import (
    NostrKeys,
    Product,
    ProductShippingCost,
    Profile,
    Stall,
    StallShippingMethod,
)
from .nostr import NostrClient, generate_keys

# Import version from pyproject.toml at runtime
try:
    __version__ = importlib.metadata.version("synvya_sdk")
except importlib.metadata.PackageNotFoundError:
    logging.warning("Package 'synvya_sdk' not found. Falling back to 'unknown'.")
    __version__ = "unknown"
except ImportError:
    logging.warning("importlib.metadata is not available. Falling back to 'unknown'.")
    __version__ = "unknown"

# Define What is Exposed at the Package Level
__all__ = [
    "NostrClient",
    "generate_keys",
    "Profile",
    "ProductShippingCost",
    "StallShippingMethod",
    "Product",
    "Stall",
    "NostrKeys",
]
