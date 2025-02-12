from typing import Any, List, Optional

from nostr_sdk import (  # type: ignore
    Event,
    EventBuilder,
    EventId,
    Events,
    Keys,
    Kind,
    Metadata,
    ProductData,
    PublicKey,
    ShippingCost,
    ShippingMethod,
    StallData,
    Timestamp,
)

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
    logger: Any

    def __init__(self, relay_url: str, nsec: Optional[str] = None) -> None: ...
    def publish_event(self, event: EventBuilder) -> EventId: ...
    def publish_note(self, content: str) -> EventId: ...
    def publish_profile(self, name: str, about: str, picture: str) -> EventId: ...
    def publish_stall(self, stall: StallData) -> EventId: ...
    def publish_product(self, product: ProductData) -> EventId: ...
    def delete_event(
        self, event_id: EventId, reason: Optional[str] = None
    ) -> EventId: ...
    def retrieve_merchants(self) -> Events: ...
    @classmethod
    def set_logging_level(cls, level: int) -> None: ...

    # Async methods
    async def _async_connect(self) -> None: ...  # Changed to None
    async def _async_publish_event(self, event_builder: EventBuilder) -> EventId: ...
    async def _async_publish_note(self, text: str) -> EventId: ...
    async def _async_publish_product(self, product: ProductData) -> EventId: ...
    async def _async_publish_profile(
        self, name: str, about: str, picture: str
    ) -> EventId: ...
    async def _async_publish_stall(self, stall: StallData) -> EventId: ...
    async def _async_retreive_merchants(self) -> Events: ...
