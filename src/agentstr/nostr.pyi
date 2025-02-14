from logging import Logger
from pathlib import Path
from typing import ClassVar, List, Optional

from nostr_sdk import (  # type: ignore
    Client,
    Event,
    EventBuilder,
    EventId,
    Events,
    Keys,
    Kind,
    Metadata,
    NostrSigner,
    ProductData,
    PublicKey,
    ShippingCost,
    ShippingMethod,
    StallData,
    Tag,
    Timestamp,
)

from agentstr.models import MerchantProduct, MerchantStall, NostrProfile

# Re-export all needed types
__all__ = [
    "Event",
    "EventBuilder",
    "Events",
    "EventId",
    "Keys",
    "Kind",
    "Metadata",
    "ProductData",
    "PublicKey",
    "ShippingCost",
    "ShippingMethod",
    "StallData",
    "Timestamp",
]

class NostrClient:
    logger: ClassVar[Logger]
    relay: str
    keys: Keys
    nostr_signer: NostrSigner
    client: Client

    def __init__(self, relay: str, nsec: str) -> None: ...
    def delete_event(
        self, event_id: EventId, reason: Optional[str] = None
    ) -> EventId: ...
    def publish_event(self, event_builder: EventBuilder) -> EventId: ...
    def publish_note(self, text: str) -> EventId: ...
    def publish_product(self, product: ProductData) -> EventId: ...
    def publish_profile(self, name: str, about: str, picture: str) -> EventId: ...
    def publish_stall(self, stall: MerchantStall) -> EventId: ...
    def retrieve_products_from_seller(
        self, public_key: str
    ) -> List[MerchantProduct]: ...
    def retrieve_stalls_from_seller(self, public_key: str) -> List[StallData]: ...
    def retrieve_sellers(self) -> set[NostrProfile]: ...
    @classmethod
    def set_logging_level(cls, logging_level: int) -> None: ...
    async def _async_connect(self) -> None: ...
    async def _async_publish_event(self, event_builder: EventBuilder) -> EventId: ...
    async def _async_publish_note(self, text: str) -> EventId: ...
    async def _async_publish_product(self, product: ProductData) -> EventId: ...
    async def _async_publish_profile(
        self, name: str, about: str, picture: str
    ) -> EventId: ...
    async def _async_publish_stall(self, stall: MerchantStall) -> EventId: ...
    async def _async_retrieve_all_stalls(self) -> Events: ...
    async def _async_retrieve_products_from_seller(
        self, seller: PublicKey
    ) -> Events: ...
    async def _async_retrieve_profile(self, author: PublicKey) -> NostrProfile: ...
    async def _async_retrieve_stalls_from_seller(self, seller: PublicKey) -> Events: ...

def generate_and_save_keys(env_var: str, env_path: Optional[Path] = None) -> Keys: ...
