"""
This module contains tests for the NostrClient class using a real Nostr relay.
"""

import logging
from typing import List

import pytest

from synvya_sdk import NostrClient, NostrKeys, Product, Stall

# Configure logging for the test module
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# used in test_nostr_integration.py
@pytest.fixture(scope="session", name="nostr_client")
def nostr_client_fixture(relay: str, merchant_keys: NostrKeys) -> NostrClient:
    """Fixture providing a NostrClient instance"""
    nostr_client = NostrClient(relay, merchant_keys.get_private_key())
    nostr_client.set_logging_level(logging.DEBUG)
    print(f"Merchant public key: {merchant_keys.get_public_key()}")
    print(f"Merchant public key hex: {merchant_keys.get_public_key(encoding='hex')}")
    return nostr_client


class TestNostrClient:
    """Test suite for NostrClient"""

    def test_set_profile(
        self,
        nostr_client: NostrClient,
        merchant_about: str,
        merchant_banner: str,
        merchant_bot: bool,
        merchant_display_name: str,
        merchant_name: str,
        merchant_nip05: str,
        merchant_picture: str,
        merchant_website: str,
    ) -> None:
        """Test setting a profile"""
        profile = nostr_client.get_profile()
        profile.set_about(merchant_about)
        profile.set_banner(merchant_banner)
        profile.set_bot(merchant_bot)
        profile.set_display_name(merchant_display_name)
        profile.set_name(merchant_name)
        profile.set_nip05(merchant_nip05)
        profile.set_picture(merchant_picture)
        profile.set_website(merchant_website)
        event_id = nostr_client.set_profile(profile)

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

    def test_delete_event(self, nostr_client: NostrClient, stalls: List[Stall]) -> None:
        """Test deleting an event"""
        # First publish something to delete
        event_id = nostr_client.set_stall(stalls[0])
        assert isinstance(event_id, str)

        # Then delete it
        delete_event_id = nostr_client.delete_event(event_id, reason="Test deletion")
        assert isinstance(delete_event_id, str)

    def test_get_products(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test retrieving products from a merchant"""
        products = nostr_client.get_products(merchant_keys.get_public_key())
        assert len(products) > 0
        for product in products:
            assert isinstance(product, Product)
            # print(f"Product: {product.name}")

    def test_get_merchants(self, nostr_client: NostrClient) -> None:
        """Test retrieving merchants"""
        try:
            merchants = nostr_client.get_merchants()
            assert len(merchants) > 0
        except RuntimeError as e:
            # print(f"\nError retrieving merchants: {e}")
            raise e

    def test_get_stalls(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test retrieving stalls from a merchant"""
        # print(f"Retrieving stalls from merchant: {merchant_keys.get_public_key()}")
        stalls = nostr_client.get_stalls(merchant_keys.get_public_key())
        assert len(stalls) > 0

    def test_get_profile_from_relay(
        self, nostr_client: NostrClient, buyer_keys: NostrKeys
    ) -> None:
        """Test async get profile from relay"""
        profile = nostr_client.get_profile(buyer_keys.get_public_key())
        assert profile is not None
        # assert profile.is_nip05_validated()

    def test_send_message(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test sending a NIP-17 message"""
        event_id = nostr_client.send_message(
            merchant_keys.get_public_key(),
            "Hello, world!",
        )
        assert isinstance(event_id, str)

    def test_receive_message(self, nostr_client: NostrClient) -> None:
        """Test receiving a NIP-17 message"""
        response = nostr_client.receive_message()
        assert isinstance(response, str)
        # await asyncio.sleep(5)
        # await nostr_client.stop_notifications()
        # Check if the task was stopped properly
        assert (
            nostr_client.notification_task is None
            or nostr_client.notification_task.done()
        )

    # @pytest.mark.asyncio
    # async def test_nostr_client_notifications(self, nostr_client: NostrClient):
    #     """
    #     Test starting and stopping async notification handling
    #     """

    #     # Start listening for notifications
    #     await nostr_client._async_listen_for_private_messages()

    #     # Let it run for a short time (simulate real-world scenario)
    #     await asyncio.sleep(5)

    #     # Stop listening
    #     await nostr_client.stop_notifications()

    #     # Check if the task was stopped properly
    #     assert (
    #         nostr_client.notification_task is None
    #         or nostr_client.notification_task.done()
    #     )
