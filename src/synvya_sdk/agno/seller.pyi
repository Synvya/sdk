from typing import ClassVar, List, Optional, Set, Tuple, Union

from pydantic import ConfigDict

from agno.tools import Toolkit
from synvya_sdk import NostrClient, Product, Profile, Stall

class MerchantTools(Toolkit):
    # Class variables
    _instances_from_create: ClassVar[Set[int]]
    model_config: ClassVar[ConfigDict]

    # Instance variables
    relays: List[str]
    private_key: str
    profile: Optional[Profile]
    nostr_client: Optional[NostrClient]
    product_db: List[Tuple[Product, Optional[str]]]
    stall_db: List[Tuple[Stall, Optional[str]]]
    _instance_id: int

    # Initialization
    def __init__(
        self,
        relays: Union[str, List[str]],
        private_key: str,
        stalls: List[Stall],
        products: List[Product],
        _from_create: bool = False,
    ) -> None: ...
    def __del__(self) -> None: ...
    @classmethod
    async def create(
        cls,
        relays: Union[str, List[str]],
        private_key: str,
        stalls: List[Stall],
        products: List[Product],
    ) -> "MerchantTools": ...
    def get_profile(self) -> str: ...
    def get_relay(self) -> str: ...
    def get_relays(self) -> List[str]: ...
    async def async_set_profile(self, profile: Profile) -> str: ...

    # Nostr NIP-15 Marketplace - Seller
    async def async_publish_product(self, product_name: str) -> str: ...
    async def async_publish_products(
        self, stall: Optional[Stall] = None, products: Optional[List[Product]] = None
    ) -> str: ...
    async def async_publish_stall(self, stall_name: str) -> str: ...
    async def async_publish_stalls(
        self, stalls: Optional[List[Stall]] = None
    ) -> str: ...
    async def async_remove_products(
        self, stall: Optional[Stall] = None, products: Optional[List[Product]] = None
    ) -> str: ...
    async def async_remove_stalls(
        self, stalls: Optional[List[Stall]] = None
    ) -> str: ...

    # Order processing
    async def async_listen_for_orders(self, timeout: int = 5) -> str: ...
    def manual_order_workflow(self, buyer: str, order: str, parameters: str) -> str: ...
    async def async_send_payment_request(
        self, buyer: str, order: str, kind: str, payment_type: str, payment_url: str
    ) -> str: ...
    async def async_send_payment_verification(
        self, buyer: str, order: str, kind: str
    ) -> str: ...
    def verify_payment(
        self,
        buyer: str,
        order: str,
        kind: str,
        payment_type: str,
        payment_url: str,
    ) -> str: ...
    # Internal database methods
    def get_products(self) -> str: ...
    def get_stalls(self) -> str: ...
    async def async_set_products(self, products: List[Product]) -> str: ...
    async def async_set_stalls(self, stalls: List[Stall]) -> str: ...

    # Internal methods
    def _message_is_order(self, message: str) -> bool: ...
    def _create_payment_request(
        self,
        order_id: str,
        payment_type: str,
        payment_url: str,
    ) -> str: ...
    def _create_payment_verification(
        self,
        order_id: str,
    ) -> str: ...
