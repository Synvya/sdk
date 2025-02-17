from typing import List

import pytest

from agentstr.models import MerchantProduct, MerchantStall
from agentstr.nostr import EventId, Keys, NostrClient


# used in test_nostr_integration.py
@pytest.fixture(scope="session")
def nostr_client(relay: str, merchant_keys: Keys) -> NostrClient:
    """Fixture providing a NostrClient instance"""
    nostr_client = NostrClient(relay, merchant_keys.secret_key().to_bech32())
    return nostr_client


class TestNostrClient:
    """Test suite for NostrClient"""

    def test_publish_profile(
        self,
        nostr_client: NostrClient,
        merchant_profile_name: str,
        merchant_profile_about: str,
        merchant_profile_picture: str,
    ) -> None:
        """Test publishing a profile"""
        event_id = nostr_client.publish_profile(
            name=merchant_profile_name,
            about=merchant_profile_about,
            picture=merchant_profile_picture,
        )
        assert isinstance(event_id, EventId)

    def test_publish_stall(
        self, nostr_client: NostrClient, merchant_stalls: List[MerchantStall]
    ) -> None:
        """Test publishing a stall"""
        event_id = nostr_client.publish_stall(merchant_stalls[0])
        assert isinstance(event_id, EventId)

    def test_publish_product(
        self, nostr_client: NostrClient, merchant_products: List[MerchantProduct]
    ) -> None:
        """Test publishing a product"""
        event_id = nostr_client.publish_product(merchant_products[0])
        assert isinstance(event_id, EventId)

    # def test_delete_event(
    #     self, nostr_client: NostrClient, test_merchant_stall: MerchantStall
    # ) -> None:
    #     """Test deleting an event"""
    #     # First publish something to delete
    #     event_id = nostr_client.publish_stall(test_merchant_stall)
    #     assert isinstance(event_id, EventId)

    #     # Then delete it
    #     delete_event_id = nostr_client.delete_event(event_id, reason="Test deletion")
    #     assert isinstance(delete_event_id, EventId)

    def test_retrieve_products_from_seller(
        self, nostr_client: NostrClient, merchant_keys: Keys
    ) -> None:
        """Test retrieving products from a seller"""
        products = nostr_client.retrieve_products_from_seller(
            merchant_keys.public_key()
        )
        assert len(products) > 0
        for product in products:
            assert isinstance(product, MerchantProduct)
            # print(f"Product: {product.name}")

    def test_retrieve_sellers(self, nostr_client: NostrClient) -> None:
        """Test retrieving sellers"""
        try:
            sellers = nostr_client.retrieve_sellers()
            assert len(sellers) > 0
        except RuntimeError as e:
            # print(f"\nError retrieving sellers: {e}")
            raise e

    def test_retrieve_stalls_from_seller(
        self, nostr_client: NostrClient, merchant_keys: Keys
    ) -> None:
        """Test retrieving stalls from a seller"""
        stalls = nostr_client.retrieve_stalls_from_seller(merchant_keys.public_key())
        assert len(stalls) > 0

    def test_retrieve_profile(
        self, nostr_client: NostrClient, merchant_keys: Keys
    ) -> None:
        """Test async retrieve profile"""
        profile = nostr_client.retrieve_profile(merchant_keys.public_key())
        assert profile is not None
