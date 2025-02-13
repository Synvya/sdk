from logging import Logger
from pathlib import Path
from typing import ClassVar, Optional

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

from agentstr.utils import Profile

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

class AgentProfile(Profile):
    WEB_URL: ClassVar[str]
    profile_url: str
    keys: Keys

    def __init__(self, keys: Keys) -> None: ...
    @classmethod
    def from_metadata(cls, metadata: Metadata, keys: Keys) -> "AgentProfile": ...
    def get_private_key(self) -> str: ...
    def get_public_key(self) -> str: ...
    def to_json(self) -> str: ...

class NostrProfile(Profile):
    WEB_URL: ClassVar[str]
    profile_url: str
    public_key: PublicKey

    def __init__(self, public_key: PublicKey) -> None: ...
    @classmethod
    def from_metadata(
        cls, metadata: Metadata, public_key: PublicKey
    ) -> "NostrProfile": ...
    def get_public_key(self) -> str: ...
    def to_json(self) -> str: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...

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
    def publish_stall(self, stall: StallData) -> EventId: ...
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
    async def _async_publish_stall(self, stall: StallData) -> EventId: ...
    async def _async_retrieve_all_stalls(self) -> Events: ...
    async def _async_retrieve_profile(self, author: PublicKey) -> NostrProfile: ...

def generate_and_save_keys(env_var: str, env_path: Optional[Path] = None) -> Keys: ...
