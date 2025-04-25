"""
This module contains tests for the BuyerTools class.
"""

import json
from typing import List, cast
from unittest.mock import AsyncMock

import pytest

from synvya_sdk import Product, Profile, Stall
from synvya_sdk.agno import BuyerTools


def test_buyer_profile_creation(
    buyer_profile: Profile,
) -> None:
    """Test the creation of a buyer profile"""
    assert buyer_profile.get_about() is not None
    assert buyer_profile.get_name() is not None
    assert buyer_profile.get_picture() is not None
    assert buyer_profile.get_website() is not None


@pytest.mark.asyncio
async def test_get_stalls(
    buyer_tools: BuyerTools,
    merchant_profile: Profile,
    stalls: List[Stall],
) -> None:
    """Test the retrieval of a seller's stalls"""
    # Type assertion to help mypy
    assert buyer_tools._nostr_client is not None

    # Get the mock client
    mock_client = buyer_tools._nostr_client

    # Use explicit cast to AsyncMock for the specific method
    async_get_stalls = cast(AsyncMock, mock_client.async_get_stalls)

    # Mock the NostrClient.async_get_stalls method
    async_get_stalls.return_value = stalls

    # Call the method and verify results
    result = await buyer_tools.async_get_stalls(merchant_profile.get_public_key())
    assert result is not None
    assert isinstance(result, str)

    # Verify the mock was called with the correct public key
    async_get_stalls.assert_called_once_with(merchant_profile.get_public_key())

    # Parse result and verify content
    result_data = json.loads(result)
    assert isinstance(result_data, list)
    assert len(result_data) == len(stalls)


@pytest.mark.asyncio
async def test_get_products(
    buyer_tools: BuyerTools,
    merchant_profile: Profile,
    products: List[Product],
) -> None:
    """Test the retrieval of a seller's products"""
    # Type assertion to help mypy
    assert buyer_tools._nostr_client is not None

    # Get the mock client
    mock_client = buyer_tools._nostr_client

    # Use explicit cast to AsyncMock for the specific method
    async_get_products = cast(AsyncMock, mock_client.async_get_products)

    # Mock the NostrClient.async_get_products method
    async_get_products.return_value = products

    # Call the method and verify results
    result = await buyer_tools.async_get_products(merchant_profile.get_public_key())
    assert isinstance(result, str)

    # Verify the mock was called with the correct parameters
    async_get_products.assert_called_once_with(merchant_profile.get_public_key(), None)

    # Parse result and verify content
    result_data = json.loads(result)
    assert isinstance(result_data, list)
    assert len(result_data) > 0
    assert isinstance(result_data[0], dict)
    assert "name" in result_data[0]
