from typing import Generator, List
from unittest.mock import Mock, patch

import pytest

from agentstr.models import MerchantProduct, MerchantStall, NostrProfile
from agentstr.nostr import EventId, Keys, Kind, NostrClient, Timestamp


@pytest.fixture
def mock_nostr_client() -> Generator[NostrClient, None, None]:
    with patch("agentstr.nostr.NostrClient") as mock_client:
        instance = mock_client.return_value
        mock_event_id = EventId(
            public_key=Keys.generate().public_key(),
            created_at=Timestamp.from_secs(1739580690),
            kind=Kind(0),
            tags=[],
            content="mock_content",
        )
        instance.publish_profile.return_value = mock_event_id
        instance.publish_stall.return_value = mock_event_id
        instance.publish_product.return_value = mock_event_id
        instance.retrieve_products_from_seller.return_value = [
            MerchantProduct(
                id="mock_id",
                stall_id="mock_stall_id",
                name="Mock Product",
                description="Mock Description",
                images=["http://example.com/image.png"],
                currency="USD",
                price=100,
                quantity=10,
                shipping=[],
            )
        ]
        instance.retrieve_sellers.return_value = [
            NostrProfile(Keys.generate().public_key())
        ]
        instance.retrieve_stalls_from_seller.return_value = [
            MerchantStall(
                id="mock_stall_id",
                name="Mock Stall",
                description="Mock Description",
                currency="USD",
                shipping=[],
                geohash="mock_geohash",
            )
        ]
        instance.retrieve_profile.return_value = NostrProfile(
            Keys.generate().public_key()
        )
        yield instance


class TestNostrClientMocked:
    """Mocked test suite for NostrClient"""

    def test_publish_profile(
        self,
        mock_nostr_client: NostrClient,
        merchant_profile_name: str,
        merchant_profile_about: str,
        merchant_profile_picture: str,
    ) -> None:
        """Test publishing a profile"""
        event_id = mock_nostr_client.publish_profile(
            name=merchant_profile_name,
            about=merchant_profile_about,
            picture=merchant_profile_picture,
        )
        assert isinstance(event_id, EventId)

    def test_publish_stall(
        self, mock_nostr_client: NostrClient, merchant_stalls: List[MerchantStall]
    ) -> None:
        """Test publishing a stall"""
        event_id = mock_nostr_client.publish_stall(merchant_stalls[0])
        assert isinstance(event_id, EventId)

    def test_publish_product(
        self, mock_nostr_client: NostrClient, merchant_products: List[MerchantProduct]
    ) -> None:
        """Test publishing a product"""
        event_id = mock_nostr_client.publish_product(merchant_products[0])
        assert isinstance(event_id, EventId)

    def test_retrieve_products_from_seller(
        self, mock_nostr_client: NostrClient, merchant_keys: Keys
    ) -> None:
        """Test retrieving products from a seller"""
        products = mock_nostr_client.retrieve_products_from_seller(
            merchant_keys.public_key()
        )
        assert len(products) > 0
        for product in products:
            assert isinstance(product, MerchantProduct)

    def test_retrieve_sellers(self, mock_nostr_client: NostrClient) -> None:
        """Test retrieving sellers"""
        sellers = mock_nostr_client.retrieve_sellers()
        assert len(sellers) > 0

    def test_retrieve_stalls_from_seller(
        self, mock_nostr_client: NostrClient, merchant_keys: Keys
    ) -> None:
        """Test retrieving stalls from a seller"""
        stalls = mock_nostr_client.retrieve_stalls_from_seller(
            merchant_keys.public_key()
        )
        assert len(stalls) > 0

    def test_retrieve_profile(
        self, mock_nostr_client: NostrClient, merchant_keys: Keys
    ) -> None:
        """Test async retrieve profile"""
        profile = mock_nostr_client.retrieve_profile(merchant_keys.public_key())
        assert profile is not None
