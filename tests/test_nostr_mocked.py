"""
Module to perform mocked tests on the NostrClient class.
Used for regular CI/CD testing without connecting to a real Nostr relay.
"""

from typing import Generator, List
from unittest.mock import patch

import pytest

from agentstr.models import AgentProfile, MerchantProduct, MerchantStall
from agentstr.nostr import EventId, Keys, NostrClient


# used in test_nostr_mocked.py
@pytest.fixture(name="nostr_client")
def mock_nostr_client(  # type: ignore[no-untyped-def]
    profile_event_id: EventId,
    stall_event_ids: List[EventId],
    product_event_ids: List[EventId],
    merchant_products: List[MerchantProduct],
    merchant_stalls: List[MerchantStall],
    merchant_profile: AgentProfile,
) -> Generator[NostrClient, None, None]:
    """
    mock NostrClient instance
    """
    with patch("agentstr.nostr.NostrClient") as mock_client:
        instance = mock_client.return_value
        # mock_event_id = EventId(
        #     public_key=Keys.generate().public_key(),
        #     created_at=Timestamp.from_secs(1739580690),
        #     kind=Kind(0),
        #     tags=[],
        #     content="mock_content",
        # )
        instance.publish_profile.return_value = profile_event_id
        instance.publish_stall.return_value = stall_event_ids[0]
        instance.publish_product.return_value = product_event_ids[0]
        instance.retrieve_products_from_seller.return_value = merchant_products
        instance.retrieve_sellers.return_value = [merchant_profile]
        instance.retrieve_stalls_from_seller.return_value = merchant_stalls
        instance.retrieve_profile.return_value = merchant_profile
        yield instance


class TestNostrClientMocked:
    """Mocked test suite for NostrClient"""

    def test_publish_profile(
        self,
        nostr_client: NostrClient,
        merchant_profile_name: str,
        merchant_profile_about: str,
        merchant_profile_picture: str,
        merchant_profile_website: str,
    ) -> None:
        """Test publishing a profile"""
        event_id = nostr_client.publish_profile(
            name=merchant_profile_name,
            about=merchant_profile_about,
            picture=merchant_profile_picture,
            website=merchant_profile_website,
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

    def test_retrieve_sellers(self, nostr_client: NostrClient) -> None:
        """Test retrieving sellers"""
        sellers = nostr_client.retrieve_sellers()
        assert len(sellers) > 0

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
