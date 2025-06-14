"""
This module contains tests for the NostrClient class using a real Nostr relay.
"""

import logging
from typing import List

import pytest

from synvya_sdk import KeyEncoding, NostrClient, NostrKeys, Product, Stall

# Configure logging for the test module
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@pytest.fixture(scope="function", name="nostr_client")
async def nostr_client_fixture(relay: str, merchant_keys: NostrKeys) -> NostrClient:
    """Async fixture providing a properly initialized NostrClient instance"""
    # Convert relay to a list for the new API, but keep backward compatibility with
    # test suite
    nostr_client = await NostrClient.create([relay], merchant_keys.get_private_key())
    nostr_client.set_logging_level(logging.DEBUG)
    print(
        f"Merchant public key: {merchant_keys.get_public_key(encoding=KeyEncoding.BECH32)}"
    )
    print(
        f"Merchant public key hex: {merchant_keys.get_public_key(encoding=KeyEncoding.HEX)}"
    )
    print(
        f"Merchant private key: {merchant_keys.get_private_key(encoding=KeyEncoding.BECH32)}"
    )
    return nostr_client


class TestNostrClient:
    """Test suite for NostrClient"""

    @pytest.mark.asyncio
    async def test_set_profile(
        self,
        nostr_client: NostrClient,
        merchant_about: str,
        merchant_banner: str,
        merchant_bot: bool,
        merchant_city: str,
        merchant_country: str,
        merchant_display_name: str,
        merchant_email: str,
        merchant_name: str,
        merchant_nip05: str,
        merchant_picture: str,
        merchant_phone: str,
        merchant_state: str,
        merchant_street: str,
        merchant_website: str,
        merchant_zip_code: str,
    ) -> None:
        """Test setting a profile"""
        profile = await nostr_client.async_get_profile()
        profile.set_about(merchant_about)
        profile.set_banner(merchant_banner)
        profile.set_bot(merchant_bot)
        profile.set_city(merchant_city)
        profile.set_country(merchant_country)

        profile.set_display_name(merchant_display_name)
        profile.set_email(merchant_email)
        profile.set_name(merchant_name)
        profile.set_nip05(merchant_nip05)
        profile.set_picture(merchant_picture)
        profile.set_phone(merchant_phone)
        profile.set_state(merchant_state)
        profile.set_street(merchant_street)
        profile.set_website(merchant_website)
        profile.set_zip_code(merchant_zip_code)

        event_id = await nostr_client.async_set_profile(profile)

        assert isinstance(event_id, str)

    @pytest.mark.asyncio
    async def test_set_stall(
        self, nostr_client: NostrClient, stalls: List[Stall]
    ) -> None:
        """Test publishing a stall"""
        event_id = await nostr_client.async_set_stall(stalls[0])
        assert isinstance(event_id, str)

    @pytest.mark.asyncio
    async def test_set_product(
        self, nostr_client: NostrClient, products: List[Product]
    ) -> None:
        """Test publishing a product"""
        event_id = await nostr_client.async_set_product(products[0])
        assert isinstance(event_id, str)

    # def test_delete_event(self, nostr_client: NostrClient, stalls: List[Stall]) -> None:
    #     """Test deleting an event"""
    #     # First publish something to delete
    #     event_id = nostr_client.set_stall(stalls[0])
    #     assert isinstance(event_id, str)

    #     # Then delete it
    #     delete_event_id = nostr_client.delete_event(event_id, reason="Test deletion")
    #     assert isinstance(delete_event_id, str)

    @pytest.mark.asyncio
    async def test_get_products(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test retrieving products from a merchant"""
        products = await nostr_client.async_get_products(merchant_keys.get_public_key())
        assert len(products) > 0
        for product in products:
            assert isinstance(product, Product)

    @pytest.mark.asyncio
    async def test_get_stalls(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test retrieving stalls from a merchant"""
        # print(f"Retrieving stalls from merchant: {merchant_keys.get_public_key()}")
        stalls = await nostr_client.async_get_stalls(merchant_keys.get_public_key())
        assert len(stalls) > 0

    @pytest.mark.asyncio
    async def test_get_merchants(self, nostr_client: NostrClient) -> None:
        """Test retrieving merchants"""
        try:
            merchants = await nostr_client.async_get_merchants()
            print(f"Merchants: {len(merchants)}")
            assert len(merchants) > 0
        except RuntimeError as e:
            # print(f"\nError retrieving merchants: {e}")
            raise e

    @pytest.mark.asyncio
    async def test_get_profile(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test async get profile from relay"""
        profile = await nostr_client.async_get_profile(merchant_keys.get_public_key())
        assert profile is not None
        # assert profile.is_nip05_validated()

    @pytest.mark.asyncio
    async def test_send_message(
        self, nostr_client: NostrClient, merchant_keys: NostrKeys
    ) -> None:
        """Test sending a NIP-17 message"""
        event_id = await nostr_client.async_send_message(
            kind="kind:14",
            key=merchant_keys.get_public_key(),
            message="Hello, world!",
        )
        assert isinstance(event_id, str)

    @pytest.mark.asyncio
    async def test_receive_message(self, nostr_client: NostrClient) -> None:
        """Test receiving a NIP-17 message"""
        response = await nostr_client.async_receive_message()
        assert isinstance(response, str)
