import logging
from logging import Logger
from typing import ClassVar, List, Optional

from agno.agent import AgentKnowledge
from agno.knowledge.json import JSONKnowledgeBase
from agno.tools import Toolkit
from synvya_sdk import NostrClient, Product, Profile, ProfileFilter, Stall

class BuyerTools(Toolkit):
    logger: ClassVar[Logger]
    sellers: set[Profile]
    relay: str
    _nostr_client: NostrClient

    # Initialization
    def __init__(
        self,
        knowledge_base: AgentKnowledge,
        relay: str,
        private_key: str,
    ) -> None: ...
    def get_profile(self) -> str: ...
    def get_relay(self) -> str: ...
    def set_profile(self, profile: Profile) -> str: ...
    def set_relay(self, relay: str) -> None: ...

    # Retrieve NIP-15 Marketplace information from Nostr
    # and store it in the local knowledge base
    def get_merchants(self) -> str: ...
    def get_merchants_in_marketplace(
        self,
        owner_public_key: str,
        name: str,
        profile_filter: Optional[ProfileFilter] = None,
    ) -> str: ...
    def get_products(
        self, merchant_public_key: str, stall: Optional[Stall] = None
    ) -> str: ...
    def get_stalls(self, merchant_public_key: str) -> str: ...

    # Query information from local knowledge base
    def get_merchants_from_knowledge_base(self) -> str: ...
    def get_products_from_knowledge_base(
        self,
        merchant_public_key: Optional[str] = None,
        categories: Optional[List[str]] = None,
    ) -> str: ...
    def get_stalls_from_knowledge_base(
        self, merchant_public_key: Optional[str] = None
    ) -> str: ...

    # Order products
    def purchase_product(self, product_name: str, quantity: int) -> str: ...

    # Internal methods
    def _get_product_from_kb(self, product_name: str) -> Product: ...
    def _store_profile_in_kb(self, profile: Profile) -> None: ...
    def _store_product_in_kb(self, product: Product) -> None: ...
    def _store_stall_in_kb(self, stall: Stall) -> None: ...
