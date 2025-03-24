"""
This module contains tests for the MerchantTools class.
"""

import itertools
import json
from typing import List
from unittest.mock import patch

from synvya_sdk import Product, Profile, Stall
from synvya_sdk.agno import MerchantTools


def test_merchant_initialization(
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


def test_publish_product(
    merchant_tools: MerchantTools,
    product_event_ids: List[str],
    products: List[Product],
) -> None:
    """Test publishing a product"""
    with patch.object(merchant_tools._nostr_client, "set_product") as mock_set_product:
        mock_set_product.return_value = product_event_ids[0]

        result = json.loads(merchant_tools.publish_product(products[0].name))
        assert result["status"] == "success"
        assert result["product_name"] == products[0].name

        result = json.loads(merchant_tools.publish_product(products[0].name))
        assert result["status"] == "success"
        assert result["product_name"] == products[0].name


def test_publish_stall(
    merchant_tools: MerchantTools,
    stall_event_ids: List[str],
    stalls: List[Stall],
) -> None:
    """Test publishing a stall by name"""
    with patch.object(merchant_tools._nostr_client, "set_stall") as mock_set_stall:
        mock_set_stall.return_value = stall_event_ids[0]

        result = json.loads(merchant_tools.publish_stall(stalls[0].name))
        assert result["status"] == "success"
        assert result["stall_name"] == stalls[0].name


def test_publish_products_in_stall(
    merchant_tools: MerchantTools,
    products_in_stall_event_ids: List[str],
    stalls: List[Stall],
) -> None:
    """Test publishing all products in a stall"""
    with patch.object(merchant_tools._nostr_client, "set_product") as mock_set_product:
        mock_set_product.return_value = itertools.cycle(products_in_stall_event_ids)

        results = json.loads(merchant_tools.publish_products(stalls[0]))
        print("Test publish products in stall")
        print(json.dumps(results, indent=4))
        assert len(results) == 2
        assert all(r["status"] == "success" for r in results)


def test_publish_all_products(
    merchant_tools: MerchantTools, product_event_ids: List[str]
) -> None:
    """Test publishing all products"""
    with patch.object(merchant_tools._nostr_client, "set_product") as mock_set_product:
        mock_set_product.return_value = itertools.cycle(product_event_ids)

        results = json.loads(merchant_tools.publish_products())
        print("Test publish all products")
        print(json.dumps(results, indent=4))
        assert len(results) == 3


def test_publish_all_stalls(
    merchant_tools: MerchantTools, stall_event_ids: List[str]
) -> None:
    """Test publishing all stalls"""
    with patch.object(merchant_tools._nostr_client, "set_stall") as mock_set_stall:
        mock_set_stall.return_value = itertools.cycle(stall_event_ids)

        results = json.loads(merchant_tools.publish_stalls())
        print("Test publish all stalls")
        print(json.dumps(results, indent=4))
        assert len(results) == 2


# def test_error_handling(merchant_tools: MerchantTools) -> None:
#     """Test error handling in various scenarios"""
#     result = json.loads(merchant_tools.publish_product("NonExistentProduct"))
#     assert result["status"] == "error"

#     results = json.loads(merchant_tools.publish_stall_by_name("NonExistentStall"))
#     assert isinstance(results, list)
#     assert results[0]["status"] == "error"

#     results = json.loads(
#         merchant_tools.publish_products_by_stall_name("NonExistentStall")
#     )
#     assert isinstance(results, list)
#     assert results[0]["status"] == "error"


def test_profile_operations(
    merchant_tools: MerchantTools,
    profile_event_id: str,
    merchant_name: str,
    merchant_about: str,
    merchant_profile: Profile,
) -> None:
    """Test profile-related operations"""
    with patch.object(merchant_tools, "get_profile") as mock_get_profile:
        mock_get_profile.return_value = json.dumps(merchant_profile.to_json())
        profile_data = json.loads(merchant_tools.get_profile())
        profile = json.loads(profile_data)  # Parse the nested JSON string
        # print(f"Profile: {profile}")
        # print(f"profile_data: {profile_data}")
        assert profile["name"] == merchant_name
        assert profile["about"] == merchant_about

    with patch.object(merchant_tools._nostr_client, "set_profile") as mock_set_profile:
        mock_set_profile.return_value = profile_event_id
        result = merchant_tools.set_profile(merchant_profile)
        assert isinstance(result, str)
