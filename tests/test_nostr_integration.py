"""
This module contains tests for the NostrClient class using a real Nostr relay.
"""

from typing import List

import pytest

from synvya_sdk import NostrClient, NostrKeys, Product, Stall


# used in test_nostr_integration.py
@pytest.fixture(scope="session", name="nostr_client")
def nostr_client_fixture(relay: str, merchant_keys: NostrKeys) -> NostrClient:
    """Fixture providing a NostrClient instance"""
    nostr_client = NostrClient(relay, merchant_keys.get_private_key())
    return nostr_client


class TestNostrClient:
    """Test suite for NostrClient"""

    def test_publish_profile(self, nostr_client: NostrClient) -> None:
        """Test publishing a profile"""
        event_id = nostr_client.publish_profile()
        assert isinstance(event_id, str)

    def test_publish_stall(
        self, nostr_client: NostrClient, stalls: List[Stall]
    ) -> None:
        """Test publishing a stall"""
        event_id = nostr_client.publish_stall(stalls[0])
        assert isinstance(event_id, str)

    def test_publish_product(
        self, nostr_client: NostrClient, products: List[Product]
    ) -> None:
        """Test publishing a product"""
        event_id = nostr_client.publish_product(products[0])
        assert isinstance(event_id, str)

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

    def test_retrieve_products_from_merchant(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test retrieving products from a merchant"""
        products = nostr_client.retrieve_products_from_merchant(
            merchant_keys.get_public_key()
        )
        assert len(products) > 0
        for product in products:
            assert isinstance(product, Product)
            # print(f"Product: {product.name}")

    def test_retrieve_merchants(self, nostr_client: NostrClient) -> None:
        """Test retrieving merchants"""
        try:
            merchants = nostr_client.retrieve_merchants()
            assert len(merchants) > 0
        except RuntimeError as e:
            # print(f"\nError retrieving merchants: {e}")
            raise e

    def test_retrieve_stalls_from_merchant(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test retrieving stalls from a merchant"""
        # print(f"Retrieving stalls from merchant: {merchant_keys.get_public_key()}")
        stalls = nostr_client.retrieve_stalls_from_merchant(
            merchant_keys.get_public_key()
        )
        assert len(stalls) > 0

    def test_retrieve_profile(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test async retrieve profile"""
        profile = nostr_client.retrieve_profile(merchant_keys.get_public_key())
        assert profile is not None
