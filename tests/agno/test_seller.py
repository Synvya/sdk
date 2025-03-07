"""
This module contains tests for the MerchantTools class.
"""

import itertools
import json
from typing import List
from unittest.mock import patch

from synvya_sdk import Product, Profile, Stall
from synvya_sdk.agno import SellerTools


def test_merchant_initialization(
    relay: str,
    seller_tools: SellerTools,
    stalls: List[Stall],
    products: List[Product],
) -> None:
    """Test merchant initialization"""
    assert seller_tools.get_profile() is not None
    assert seller_tools.get_relay() == relay

    products_output = json.loads(seller_tools.get_products())
    assert len(products_output) == len(products)

    stalls_output = json.loads(seller_tools.get_stalls())
    assert len(stalls_output) == len(stalls)
    assert stalls_output[0]["name"] == stalls[0].name


def test_publish_product_by_name(
    seller_tools: SellerTools,
    product_event_ids: List[str],
    products: List[Product],
) -> None:
    """Test publishing a product by name"""
    with patch.object(seller_tools._nostr_client, "publish_product") as mock_publish:
        mock_publish.return_value = product_event_ids[0]

        result = json.loads(seller_tools.publish_product_by_name(products[0].name))
        assert result["status"] == "success"
        assert result["product_name"] == products[0].name

        result = json.loads(
            seller_tools.publish_product_by_name(json.dumps({"name": products[0].name}))
        )
        assert result["status"] == "success"
        assert result["product_name"] == products[0].name


def test_publish_stall_by_name(
    seller_tools: SellerTools,
    stall_event_ids: List[str],
    stalls: List[Stall],
) -> None:
    """Test publishing a stall by name"""
    with patch.object(seller_tools._nostr_client, "publish_stall") as mock_publish:
        mock_publish.return_value = stall_event_ids[0]

        result = json.loads(seller_tools.publish_stall_by_name(stalls[0].name))
        assert result["status"] == "success"
        assert result["stall_name"] == stalls[0].name


def test_publish_products_by_stall_name(
    seller_tools: SellerTools,
    product_event_ids: List[str],
    stalls: List[Stall],
) -> None:
    """Test publishing all products in a stall"""
    with patch.object(seller_tools._nostr_client, "publish_product") as mock_publish:
        mock_publish.side_effect = itertools.cycle(product_event_ids)

        results = json.loads(
            seller_tools.publish_products_by_stall_name(stalls[0].name)
        )
        assert len(results) == 2
        assert all(r["status"] == "success" for r in results)


def test_publish_all_products(
    seller_tools: SellerTools, product_event_ids: List[str]
) -> None:
    """Test publishing all products"""
    with patch.object(seller_tools._nostr_client, "publish_product") as mock_publish:
        mock_publish.side_effect = itertools.cycle(product_event_ids)

        results = json.loads(seller_tools.publish_all_products())
        assert len(results) == 3


def test_publish_all_stalls(
    seller_tools: SellerTools, stall_event_ids: List[str]
) -> None:
    """Test publishing all stalls"""
    with patch.object(seller_tools._nostr_client, "publish_stall") as mock_publish:
        mock_publish.side_effect = itertools.cycle(stall_event_ids)

        results = json.loads(seller_tools.publish_all_stalls())
        assert len(results) == 2


def test_error_handling(seller_tools: SellerTools) -> None:
    """Test error handling in various scenarios"""
    result = json.loads(seller_tools.publish_product_by_name("NonExistentProduct"))
    assert result["status"] == "error"

    results = json.loads(seller_tools.publish_stall_by_name("NonExistentStall"))
    assert isinstance(results, list)
    assert results[0]["status"] == "error"

    results = json.loads(
        seller_tools.publish_products_by_stall_name("NonExistentStall")
    )
    assert isinstance(results, list)
    assert results[0]["status"] == "error"


def test_profile_operations(
    seller_tools: SellerTools,
    profile_event_id: str,
    merchant_name: str,
    merchant_about: str,
    merchant_profile: Profile,
) -> None:
    """Test profile-related operations"""
    with patch.object(seller_tools._nostr_client, "get_profile") as mock_get_profile:
        mock_get_profile.return_value = merchant_profile
        profile_data = json.loads(seller_tools.get_profile())
        profile = json.loads(profile_data)  # Parse the nested JSON string
        # print(f"Profile: {profile}")
        assert profile["name"] == merchant_name
        assert profile["about"] == merchant_about

    with patch.object(seller_tools._nostr_client, "publish_profile") as mock_publish:
        mock_publish.return_value = profile_event_id
        result = seller_tools.publish_profile()
        assert isinstance(result, str)
