import logging
from logging import Logger
from typing import Any, ClassVar, Dict, List, Optional, Set, Union

from agno.agent import AgentKnowledge
from agno.tools import Toolkit
from synvya_sdk import NostrClient, Product, Profile, ProfileFilter, Stall

class BuyerTools(Toolkit):
    # Class variables
    _instances_from_create: ClassVar[Set[int]]
    merchants: Set[Profile]

    # Instance variables
    relays: List[str]
    private_key: str
    knowledge_base: AgentKnowledge
    _nostr_client: Optional[NostrClient]
    profile: Optional[Profile]
    _instance_id: int

    # Initialization
    def __init__(
        self,
        knowledge_base: AgentKnowledge,
        relays: Union[str, List[str]],
        private_key: str,
        _from_create: bool = False,
    ) -> None: ...
    def __del__(self) -> None: ...
    @classmethod
    async def create(
        cls,
        knowledge_base: AgentKnowledge,
        relays: Union[str, List[str]],
        private_key: str,
        log_level: Optional[int] = logging.INFO,
    ) -> "BuyerTools": ...
    def get_profile(self) -> str: ...
    def get_relay(self) -> str: ...
    def get_relays(self) -> List[str]: ...
    async def async_set_profile(self, profile: Profile) -> str: ...

    # Retrieve NIP-15 Marketplace information from Nostr
    # and store it in the local knowledge base
    async def async_get_merchants(
        self, profile_filter_json: Optional[str | dict] = None
    ) -> str: ...
    async def async_get_merchants_in_marketplace(
        self,
        owner_public_key: str,
        name: str,
        profile_filter: Optional[ProfileFilter] = None,
    ) -> str: ...
    async def async_get_products(
        self, merchant_public_key: str, stall: Optional[Stall] = None
    ) -> str: ...
    async def async_get_stalls(self, merchant_public_key: str) -> str: ...

    # Query information from local knowledge base
    def get_merchants_from_knowledge_base(
        self, profile_filter_json: Optional[str | dict] = None
    ) -> str: ...
    def get_products_from_knowledge_base(
        self,
        merchant_public_key: Optional[str] = None,
        categories: Optional[List[str]] = None,
    ) -> str: ...
    def get_stalls_from_knowledge_base(
        self, merchant_public_key: Optional[str] = None
    ) -> str: ...

    # Order products
    async def async_submit_order(self, product_name: str, quantity: int) -> str: ...
    async def async_listen_for_message(self, timeout: int = 5) -> str: ...
    async def async_submit_payment(self, payment_request: str) -> str: ...
    # Internal methods
    def _get_product_from_kb(self, product_name: str) -> Product: ...
    def _store_profile_in_kb(self, profile: Profile) -> None: ...
    def _store_product_in_kb(self, product: Product) -> None: ...
    def _store_stall_in_kb(self, stall: Stall) -> None: ...
    def _message_is_payment_request(self, message: str) -> bool: ...
    def _message_is_payment_verification(self, message: str) -> bool: ...
    @staticmethod
    def _normalize_hashtag(tag: str) -> str: ...
