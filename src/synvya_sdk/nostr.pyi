"""
Type stubs for the Nostr module.

This file provides type annotations for the Nostr module, enabling better
type checking and autocompletion in IDEs. It defines the expected types
for classes, functions, and variables used within the Nostr module.

Note: This is a type stub file and does not contain any executable code.
"""

import asyncio
from logging import Logger
from pathlib import Path
from typing import ClassVar, List, Optional

from nostr_sdk import (  # type: ignore
    Client,
    Event,
    EventBuilder,
    EventId,
    Events,
    Filter,
    HandleNotification,
    Keys,
    NostrSigner,
    PublicKey,
    RelayMessage,
    UnsignedEvent,
)

from .models import NostrKeys, Product, Profile, ProfileFilter, Stall

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
    notification_task: Optional[asyncio.Task]
    received_eose: bool
    private_message: UnsignedEvent = None
    direct_message: Event = None

    # Initialization methods
    def __init__(self, relay: str, private_key: str) -> None: ...
    @classmethod
    def set_logging_level(cls, logging_level: int) -> None: ...
    def get_profile(self, public_key: Optional[str] = None) -> Profile: ...
    def set_profile(self, profile: Profile) -> str: ...

    # Nostr generic methods
    def delete_event(self, event_id: str, reason: Optional[str] = None) -> str: ...
    def publish_event(self, kind: int, content: str) -> str: ...
    def publish_note(self, text: str) -> str: ...
    def receive_message(self) -> str: ...
    def send_message(self, public_key: str, message: str) -> str: ...

    # NIP-15 Marketplace - Buyer
    def get_merchants(
        self, profile_filter: Optional[ProfileFilter] = None
    ) -> set[Profile]: ...
    def get_merchants_in_marketplace(
        self,
        marketplace_owner: str,
        marketplace_name: str,
        profile_filter: Optional[ProfileFilter] = None,
    ) -> set[Profile]: ...
    def get_products(
        self, merchant: str, stall: Optional[Stall] = None
    ) -> List[Product]: ...
    def get_stalls(self, merchant: str) -> List[Stall]: ...

    # NIP-15 Marketplace - Seller

    def set_product(self, product: Product) -> str: ...
    def set_stall(self, stall: Stall) -> str: ...
    def stop_notifications(self) -> None: ...

    # Internal methods
    async def _async_connect(self) -> None: ...
    async def _async_get_events(self, events_filter: Filter) -> Events: ...
    async def _async_get_products(
        self, merchant: PublicKey, stall: Optional[Stall] = None
    ) -> Events: ...
    async def _async_get_profile_from_relay(
        self, profile_key: PublicKey
    ) -> Profile: ...
    async def _async_get_stalls(
        self, merchant: Optional[PublicKey] = None
    ) -> Events: ...
    async def _async_publish_event(self, event_builder: EventBuilder) -> EventId: ...
    async def _async_publish_note(self, text: str) -> EventId: ...
    async def _async_receive_message(self) -> str: ...
    async def _async_send_message(
        self, public_key: PublicKey, message: str
    ) -> EventId: ...
    async def _async_set_product(self, product: Product) -> EventId: ...
    async def _async_set_profile(self) -> EventId: ...
    async def _async_set_stall(self, stall: Stall) -> EventId: ...
    async def _async_start_notifications(self) -> None: ...

    class MyNotificationHandler(HandleNotification):
        def __init__(self, nostr_client: NostrClient): ...
        async def handle_msg(self, relay_url: str, msg: RelayMessage) -> None: ...
        async def handle(
            self, relay_url: str, subscription_id: str, event: Event
        ) -> None: ...

def generate_keys(env_var: str, env_path: Optional[Path] = None) -> NostrKeys: ...
