"""
This module contains tests for the MerchantTools class.
"""

import itertools as it
import json
from typing import List, cast
from unittest.mock import AsyncMock

import pytest

from synvya_sdk import Product, Profile, Stall
from synvya_sdk.agno import MerchantTools


@pytest.mark.asyncio
async def test_merchant_initialization(
    relay: str,
    merchant_tools: MerchantTools,
    stalls: List[Stall],
    products: List[Product],
) -> None:
    """Test merchant initialization"""
    assert merchant_tools.get_profile() is not None
    assert merchant_tools.get_relay() == relay

    products_output = json.loads(merchant_tools.get_products())
    assert len(products_output) == len(products)

    stalls_output = json.loads(merchant_tools.get_stalls())
    assert len(stalls_output) == len(stalls)
    assert stalls_output[0]["name"] == stalls[0].name


@pytest.mark.asyncio
async def test_publish_product(
    merchant_tools: MerchantTools,
    product_event_ids: List[str],
    products: List[Product],
) -> None:
    """Test publishing a product"""
    # Type assertion to help mypy
    assert merchant_tools.nostr_client is not None

    # Get the mock client
    mock_client = merchant_tools.nostr_client

    # Use explicit cast to AsyncMock for the specific method
    async_set_product = cast(AsyncMock, mock_client.async_set_product)
    async_set_product.return_value = product_event_ids[0]

    result = json.loads(await merchant_tools.async_publish_product(products[0].name))
    assert result["status"] == "success"
    assert result["product_name"] == products[0].name

    result = json.loads(await merchant_tools.async_publish_product(products[0].name))
    assert result["status"] == "success"
    assert result["product_name"] == products[0].name


@pytest.mark.asyncio
async def test_publish_stall(
    merchant_tools: MerchantTools,
    stall_event_ids: List[str],
    stalls: List[Stall],
) -> None:
    """Test publishing a stall by name"""
    # Type assertion to help mypy
    assert merchant_tools.nostr_client is not None

    # Get the mock client
    mock_client = merchant_tools.nostr_client

    # Use explicit cast to AsyncMock for the specific method
    async_set_stall = cast(AsyncMock, mock_client.async_set_stall)
    async_set_stall.return_value = stall_event_ids[0]

    result = json.loads(await merchant_tools.async_publish_stall(stalls[0].name))
    assert result["status"] == "success"
    assert result["stall_name"] == stalls[0].name


@pytest.mark.asyncio
async def test_publish_products_in_stall(
    merchant_tools: MerchantTools,
    products_in_stall_event_ids: List[str],
    stalls: List[Stall],
) -> None:
    """Test publishing all products in a stall"""
    # Type assertion to help mypy
    assert merchant_tools.nostr_client is not None

    # Get the mock client
    mock_client = merchant_tools.nostr_client

    # Create a generator that cycles through the event IDs
    event_id_generator = it.cycle(products_in_stall_event_ids)

    # Use explicit cast to AsyncMock for the specific method
    async_set_product = cast(AsyncMock, mock_client.async_set_product)

    # Set up the mock to return different event IDs for each call
    async_set_product.side_effect = lambda *args, **kwargs: next(event_id_generator)

    results = json.loads(await merchant_tools.async_publish_products(stalls[0]))
    print("Test publish products in stall")
    print(json.dumps(results, indent=4))
    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)


@pytest.mark.asyncio
async def test_publish_all_products(
    merchant_tools: MerchantTools, product_event_ids: List[str]
) -> None:
    """Test publishing all products"""
    # Type assertion to help mypy
    assert merchant_tools.nostr_client is not None

    # Get the mock client
    mock_client = merchant_tools.nostr_client

    # Create a generator that cycles through the event IDs
    event_id_generator = it.cycle(product_event_ids)

    # Use explicit cast to AsyncMock for the specific method
    async_set_product = cast(AsyncMock, mock_client.async_set_product)

    # Set up the mock to return different event IDs for each call
    async_set_product.side_effect = lambda *args, **kwargs: next(event_id_generator)

    results = json.loads(await merchant_tools.async_publish_products())
    print("Test publish all products")
    print(json.dumps(results, indent=4))
    assert len(results) == 3


@pytest.mark.asyncio
async def test_publish_all_stalls(
    merchant_tools: MerchantTools, stall_event_ids: List[str]
) -> None:
    """Test publishing all stalls"""
    # Type assertion to help mypy
    assert merchant_tools.nostr_client is not None

    # Get the mock client
    mock_client = merchant_tools.nostr_client

    # Create a generator that cycles through the event IDs
    event_id_generator = it.cycle(stall_event_ids)

    # Use explicit cast to AsyncMock for the specific method
    async_set_stall = cast(AsyncMock, mock_client.async_set_stall)

    # Set up the mock to return different event IDs for each call
    async_set_stall.side_effect = lambda *args, **kwargs: next(event_id_generator)

    results = json.loads(await merchant_tools.async_publish_stalls())
    print("Test publish all stalls")
    print(json.dumps(results, indent=4))
    assert len(results) == 2


@pytest.mark.asyncio
async def test_profile_operations(
    merchant_tools: MerchantTools,
    profile_event_id: str,
    merchant_name: str,
    merchant_about: str,
    merchant_profile: Profile,
) -> None:
    """Test profile-related operations"""
    # No need to mock get_profile since we're not testing it directly
    profile_data = json.loads(merchant_tools.get_profile())
    assert "name" in profile_data
    assert "about" in profile_data

    # Type assertion to help mypy
    assert merchant_tools.nostr_client is not None

    # Get the mock client
    mock_client = merchant_tools.nostr_client

    # Use explicit cast to AsyncMock for the specific method
    async_set_profile = cast(AsyncMock, mock_client.async_set_profile)
    async_set_profile.return_value = profile_event_id

    result = await merchant_tools.async_set_profile(merchant_profile)
    assert isinstance(result, str)
