"""
Type stubs for the Nostr module.

This file provides type annotations for the Nostr module, enabling better
type checking and autocompletion in IDEs. It defines the expected types
for classes, functions, and variables used within the Nostr module.

Note: This is a type stub file and does not contain any executable code.
"""

from logging import Logger
from pathlib import Path
from typing import ClassVar, List, Optional, Union

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
    relays: List[str]
    keys: Keys
    nostr_signer: NostrSigner
    client: Client
    connected: bool
    profile: Profile

    # Initialization methods
    def __init__(
        self,
        relays: Union[str, List[str]],
        private_key: str,
        _from_create: bool = False,
    ) -> None: ...
    def __del__(self) -> None: ...
    # Asynchronous factory method for proper initialization
    @classmethod
    async def create(
        cls, relays: Union[str, List[str]], private_key: str
    ) -> "NostrClient": ...
    @classmethod
    def set_logging_level(cls, logging_level: int) -> None: ...

    # Asynchronous methods
    async def async_delete_event(
        self, event_id: str, reason: Optional[str] = None
    ) -> str: ...
    async def async_get_agents(self, profile_filter: ProfileFilter) -> set[Profile]: ...
    async def async_get_merchants(
        self, profile_filter: Optional[ProfileFilter] = None
    ) -> set[Profile]: ...
    async def async_get_merchants_in_marketplace(
        self,
        marketplace_owner: str,
        marketplace_name: str,
        profile_filter: Optional[ProfileFilter] = None,
    ) -> set[Profile]: ...
    async def async_get_products(
        self, merchant: str, stall: Optional[Stall] = None
    ) -> List[Product]: ...
    async def async_get_profile(self, public_key: Optional[str] = None) -> Profile: ...
    async def async_get_stalls(self, merchant: Optional[str] = None) -> List[Stall]: ...
    async def async_publish_note(self, text: str) -> str: ...
    async def async_receive_message(self, timeout: Optional[int] = 15) -> str: ...
    async def async_send_message(self, kind: str, key: str, message: str) -> str: ...
    async def async_set_product(self, product: Product) -> str: ...
    async def async_set_profile(self, profile: Profile) -> str: ...
    async def async_set_stall(self, stall: Stall) -> str: ...
    async def async_subscribe_to_messages(self) -> str: ...
    async def async_nip96_upload(
        self,
        server_url: str,
        file_data: bytes,
        mime_type: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> str: ...

    # Sync wrappers for sync users
    def delete_event(self, event_id: str, reason: Optional[str] = None) -> str: ...
    def get_agents(self, profile_filter: ProfileFilter) -> set[Profile]: ...
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
    def get_profile(self, public_key: Optional[str] = None) -> Profile: ...
    def get_stalls(self, merchant: str) -> List[Stall]: ...
    def publish_note(self, text: str) -> str: ...
    def receive_message(self, timeout: Optional[int] = 15) -> str: ...
    def send_message(self, kind: str, public_key: str, message: str) -> str: ...
    def set_profile(self, profile: Profile) -> str: ...
    def set_stall(self, stall: Stall) -> str: ...
    def subscribe_to_messages(self) -> str: ...
    def set_product(self, product: Product) -> str: ...
    def nip96_upload(
        self,
        server_url: str,
        file_data: bytes,
        mime_type: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> str: ...

    # Internal methods
    async def _async_connect(self) -> None: ...

def generate_keys(env_var: str, env_path: Optional[Path] = None) -> NostrKeys: ...
