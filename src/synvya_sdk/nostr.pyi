"""
Type stubs for the Nostr module.

This file provides type annotations for the Nostr module, enabling better
type checking and autocompletion in IDEs. It defines the expected types
for classes, functions, and variables used within the Nostr module.

Note: This is a type stub file and does not contain any executable code.
"""

from logging import Logger
from pathlib import Path
from typing import ClassVar, List, Optional

from nostr_sdk import (  # type: ignore
    Client,
    EventBuilder,
    EventId,
    Events,
    Filter,
    Keys,
    NostrSigner,
    PublicKey,
)

from .models import NostrKeys, Product, Profile, Stall

# Re-export all needed types
# __all__ = [
#     "Event",
#     "EventBuilder",
#     "Events",
#     "EventId",
#     "Keys",
#     "Kind",
#     "Metadata",
#     "ProductData",
#     "PublicKey",
#     "ShippingCost",
#     "ShippingMethod",
#     "StallData",
#     "Timestamp",
# ]

class NostrClient:
    """
    NostrClient implements the set of Nostr utilities required for higher level functions
    implementations like the Marketplace.
    """

    logger: ClassVar[Logger]
    relay: str
    keys: Keys
    nostr_signer: NostrSigner
    client: Client
    connected: bool
    profile: Profile

    def __init__(self, relay: str, private_key: str) -> None: ...
    def delete_event(self, event_id: str, reason: Optional[str] = None) -> str: ...
    # def publish_event(self, event_builder: EventBuilder) -> EventId: ...
    def get_profile(self) -> Profile: ...
    def publish_note(self, text: str) -> str: ...
    def publish_product(self, product: Product) -> str: ...
    def publish_profile(self) -> str: ...
    def publish_stall(self, stall: Stall) -> str: ...
    def retrieve_marketplace_merchants(
        self, owner: str, marketplace_name: str
    ) -> set[Profile]: ...
    def retrieve_products_from_merchant(self, merchant: str) -> List[Product]: ...
    def retrieve_profile(self, public_key: str) -> Profile: ...
    def retrieve_stalls_from_merchant(self, merchant: str) -> List[Stall]: ...
    def retrieve_merchants(self) -> set[Profile]: ...
    @classmethod
    def set_logging_level(cls, logging_level: int) -> None: ...
    async def _async_connect(self) -> None: ...
    async def _async_publish_event(self, event_builder: EventBuilder) -> EventId: ...
    async def _async_publish_note(self, text: str) -> EventId: ...
    async def _async_publish_product(self, product: Product) -> EventId: ...
    async def _async_publish_profile(self) -> EventId: ...
    async def _async_publish_stall(self, stall: Stall) -> EventId: ...
    async def _async_retrieve_all_stalls(self) -> Events: ...
    async def _async_retrieve_events(self, events_filter: Filter) -> Events: ...
    async def _async_retrieve_products_from_merchant(
        self, merchant: PublicKey
    ) -> Events: ...
    async def _async_retrieve_profile(self, author: PublicKey) -> Profile: ...
    async def _async_retrieve_stalls_from_seller(self, seller: PublicKey) -> Events: ...

def generate_keys(env_var: str, env_path: Optional[Path] = None) -> NostrKeys: ...
