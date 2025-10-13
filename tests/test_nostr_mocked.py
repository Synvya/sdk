"""
Module to perform mocked tests on the NostrClient class.
Used for regular CI/CD testing without connecting to a real Nostr relay.
"""

from typing import Generator, List
from unittest.mock import patch

import pytest
from nostr_sdk import EventId

from synvya_sdk import KeyEncoding, NostrClient, NostrKeys, Product, Profile, Stall
from synvya_sdk.models import ClassifiedListing


# used in test_nostr_mocked.py
@pytest.fixture(name="nostr_client")
def mock_nostr_client(  # type: ignore[no-untyped-def]
    profile_event_id: str,
    stall_event_ids: List[EventId],
    product_event_ids: List[EventId],
    products: List[Product],
    stalls: List[Stall],
    merchant_profile: Profile,
    classified_listings: List[ClassifiedListing],
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
        instance.get_classified_listings.return_value = classified_listings
        instance.async_get_classified_listings.return_value = classified_listings
        yield instance


class TestNostrKeys:
    """Test NostrKeys"""

    def test_init_new(self) -> None:
        """Test NostrKeys initialization"""
        keys = NostrKeys()
        assert keys is not None

    def test_init_hex(self, merchant_keys: NostrKeys) -> None:
        """Test NostrKeys initialization with hex key"""
        keys = NostrKeys(merchant_keys.get_private_key(KeyEncoding.HEX))
        assert keys is not None

    def test_init_bech32(self, merchant_keys: NostrKeys) -> None:
        """Test NostrKeys initialization with bech32 key"""
        keys = NostrKeys(merchant_keys.get_private_key(KeyEncoding.BECH32))
        assert keys is not None

    def test_get_public_key(self) -> None:
        """Test NostrKeys get_public_key"""
        keys = NostrKeys()
        assert keys.get_public_key(KeyEncoding.BECH32) is not None

    def test_get_private_key(self) -> None:
        """Test NostrKeys get_private_key"""
        keys = NostrKeys()
        assert keys.get_private_key(KeyEncoding.BECH32) is not None


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

    def test_get_profile(self, nostr_client: NostrClient) -> None:
        """Test get profile"""
        profile = nostr_client.get_profile()
        assert profile is not None

    def test_classified_listings_fixture(
        self, classified_listings: List[ClassifiedListing]
    ) -> None:
        """Validate parsed classified listing examples"""
        assert len(classified_listings) >= 1
        for listing in classified_listings:
            assert isinstance(listing, ClassifiedListing)
            assert listing.title
            assert listing.price_currency == "USD"
        categories = {
            category
            for listing in classified_listings
            for category in listing.categories
        }
        assert "gluten-free" in categories

    def test_get_classified_listings(
        self,
        nostr_client: NostrClient,
        merchant_keys: NostrKeys,
        classified_listings: List[ClassifiedListing],
    ) -> None:
        """Test retrieving classified listings via the mocked client"""
        listings = nostr_client.get_classified_listings(merchant_keys.get_public_key())
        assert listings == classified_listings
        assert all(isinstance(listing, ClassifiedListing) for listing in listings)

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
