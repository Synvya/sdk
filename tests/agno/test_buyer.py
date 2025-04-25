"""
This module contains tests for the BuyerTools class.
"""

import json
from typing import List
from unittest.mock import patch

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


# This test will download all merchants from the relay. Expect it to run for long.
# @pytest.mark.asyncio
# async def test_get_merchants(
#     buyer_tools: BuyerTools,
# ) -> None:
#     """Test the retrieval of merchants"""
#     result = await buyer_tools.async_get_merchants()
#     assert result is not None


# def test_get_sellers_by_location(
#     buyer_tools: BuyerTools, merchant_location: str, merchant_name: str
# ) -> None:
#     """Test the finding of sellers by location"""
#     with patch(
#         "synvya_sdk.agno.buyer._map_location_to_geohash"
#     ) as mock_map_location_to_geohash:
#         mock_map_location_to_geohash.return_value = "000000000"

#         result = buyer_tools.get_sellers_by_location(merchant_location)
#         assert result is not None
#         assert merchant_name in result


@pytest.mark.asyncio
async def test_get_stalls(
    buyer_tools: BuyerTools,
    merchant_profile: Profile,
    stalls: List[Stall],
) -> None:
    """Test the retrieval of a seller's stalls"""
    # Mock the NostrClient.async_get_stalls method
    buyer_tools._nostr_client.async_get_stalls.return_value = stalls

    # Call the method and verify results
    result = await buyer_tools.async_get_stalls(merchant_profile.get_public_key())
    assert result is not None
    assert isinstance(result, str)

    # Verify the mock was called with the correct public key
    buyer_tools._nostr_client.async_get_stalls.assert_called_once_with(
        merchant_profile.get_public_key()
    )

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
    # Mock the NostrClient.async_get_products method
    buyer_tools._nostr_client.async_get_products.return_value = products

    # Call the method and verify results
    result = await buyer_tools.async_get_products(merchant_profile.get_public_key())
    assert isinstance(result, str)

    # Verify the mock was called with the correct parameters
    buyer_tools._nostr_client.async_get_products.assert_called_once_with(
        merchant_profile.get_public_key(), None
    )

    # Parse result and verify content
    result_data = json.loads(result)
    assert isinstance(result_data, list)
    assert len(result_data) > 0
    assert isinstance(result_data[0], dict)
    assert "name" in result_data[0]
