"""
Module to perform mocked tests on the NostrClient class.
Used for regular CI/CD testing without connecting to a real Nostr relay.
"""

from typing import Generator, List
from unittest.mock import patch

import pytest
from nostr_sdk import EventId

from synvya_sdk import NostrClient, NostrKeys, Product, Profile, Stall


# used in test_nostr_mocked.py
@pytest.fixture(name="nostr_client")
def mock_nostr_client(  # type: ignore[no-untyped-def]
    profile_event_id: str,
    stall_event_ids: List[EventId],
    product_event_ids: List[EventId],
    products: List[Product],
    stalls: List[Stall],
    merchant_profile: Profile,
) -> Generator[NostrClient, None, None]:
    """
    mock NostrClient instance
    """
    with patch("synvya_sdk.NostrClient") as mock_client:
        instance = mock_client.return_value
        instance.profile = merchant_profile
        instance.publish_profile.return_value = profile_event_id
        instance.publish_stall.return_value = stall_event_ids[0]
        instance.publish_product.return_value = product_event_ids[0]
        instance.retrieve_products_from_merchant.return_value = products
        instance.retrieve_all_merchants.return_value = [merchant_profile]
        instance.retrieve_stalls_from_merchant.return_value = stalls
        instance.retrieve_profile.return_value = merchant_profile
        yield instance


class TestNostrClientMocked:
    """Mocked test suite for NostrClient"""

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

    def test_retrieve_products_from_seller(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test retrieving products from a merchant"""
        products = nostr_client.retrieve_products_from_merchant(
            merchant_keys.get_public_key()
        )
        assert len(products) > 0
        for product in products:
            assert isinstance(product, Product)

    def test_retrieve_all_merchants(self, nostr_client: NostrClient) -> None:
        """Test retrieving all merchants"""
        merchants = nostr_client.retrieve_all_merchants()
        assert len(merchants) > 0

    def test_retrieve_stalls_from_merchant(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test retrieving stalls from a merchant"""
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
