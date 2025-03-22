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
        instance.set_profile.return_value = profile_event_id
        instance.set_stall.return_value = stall_event_ids[0]
        instance.set_product.return_value = product_event_ids[0]
        instance.get_products.return_value = products
        instance.get_merchants.return_value = [merchant_profile]
        instance.get_stalls.return_value = stalls
        instance.get_profile.return_value = merchant_profile
        yield instance


class TestNostrClientMocked:
    """Mocked test suite for NostrClient"""

    def test_set_profile(
        self, nostr_client: NostrClient, merchant_profile: Profile
    ) -> None:
        """Test publishing a profile"""
        event_id = nostr_client.set_profile(merchant_profile)
        assert isinstance(event_id, str)

    def test_set_stall(self, nostr_client: NostrClient, stalls: List[Stall]) -> None:
        """Test publishing a stall"""
        event_id = nostr_client.set_stall(stalls[0])
        assert isinstance(event_id, str)

    def test_set_product(
        self, nostr_client: NostrClient, products: List[Product]
    ) -> None:
        """Test publishing a product"""
        event_id = nostr_client.set_product(products[0])
        assert isinstance(event_id, str)

    def test_get_products(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test retrieving products from a merchant"""
        products = nostr_client.get_products(merchant_keys.get_public_key())
        assert len(products) > 0
        for product in products:
            assert isinstance(product, Product)

    def test_get_merchants(self, nostr_client: NostrClient) -> None:
        """Test retrieving all merchants"""
        merchants = nostr_client.get_merchants()
        assert len(merchants) > 0

    def test_get_stalls(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test retrieving stalls from a merchant"""
        stalls = nostr_client.get_stalls(merchant_keys.get_public_key())
        assert len(stalls) > 0

    def test_get_profile(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test get profile"""
        profile = nostr_client.get_profile()
        assert profile is not None

    def test_profile_operations(self, merchant_profile: Profile) -> None:
        """Test profile operations"""
        profile_json_str: str = merchant_profile.to_json()
        assert isinstance(profile_json_str, str)
        profile = Profile.from_json(profile_json_str)
        assert profile is not None
        assert profile.get_public_key() == merchant_profile.get_public_key()

        assert profile.get_about() == merchant_profile.get_about()
        assert profile.get_banner() == merchant_profile.get_banner()
        assert profile.get_display_name() == merchant_profile.get_display_name()
        assert profile.get_locations() == merchant_profile.get_locations()
        assert profile.get_name() == merchant_profile.get_name()
        assert profile.get_picture() == merchant_profile.get_picture()
        assert profile.get_website() == merchant_profile.get_website()
