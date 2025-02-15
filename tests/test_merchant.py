import itertools
import json
from typing import List
from unittest.mock import patch

from agentstr.merchant import Merchant
from agentstr.models import MerchantProduct, MerchantStall
from agentstr.nostr import EventId


def test_merchant_initialization(
    relay: str,
    merchant: Merchant,
    merchant_stalls: List[MerchantStall],
    merchant_products: List[MerchantProduct],
) -> None:
    """Test merchant initialization"""
    assert merchant.get_profile() is not None
    assert merchant.get_relay() == relay

    products = json.loads(merchant.get_products())
    assert len(products) == len(merchant_products)

    stalls = json.loads(merchant.get_stalls())
    assert len(stalls) == len(merchant_stalls)
    assert stalls[0]["name"] == merchant_stalls[0].name


def test_publish_product_by_name(
    merchant: Merchant,
    product_event_ids: List[EventId],
    merchant_products: List[MerchantProduct],
) -> None:
    """Test publishing a product by name"""
    with patch.object(merchant._nostr_client, "publish_product") as mock_publish:
        mock_publish.return_value = product_event_ids[0]

        result = json.loads(merchant.publish_product_by_name(merchant_products[0].name))
        assert result["status"] == "success"
        assert result["product_name"] == merchant_products[0].name

        result = json.loads(
            merchant.publish_product_by_name(
                json.dumps({"name": merchant_products[0].name})
            )
        )
        assert result["status"] == "success"
        assert result["product_name"] == merchant_products[0].name


def test_publish_stall_by_name(
    merchant: Merchant,
    stall_event_ids: List[EventId],
    merchant_stalls: List[MerchantStall],
) -> None:
    """Test publishing a stall by name"""
    with patch.object(merchant._nostr_client, "publish_stall") as mock_publish:
        mock_publish.return_value = stall_event_ids[0]

        result = json.loads(merchant.publish_stall_by_name(merchant_stalls[0].name))
        assert result["status"] == "success"
        assert result["stall_name"] == merchant_stalls[0].name


def test_publish_products_by_stall_name(
    merchant: Merchant,
    product_event_ids: List[EventId],
    merchant_stalls: List[MerchantStall],
) -> None:
    """Test publishing all products in a stall"""
    with patch.object(merchant._nostr_client, "publish_product") as mock_publish:
        mock_publish.side_effect = itertools.cycle(product_event_ids)

        results = json.loads(
            merchant.publish_products_by_stall_name(merchant_stalls[0].name)
        )
        assert len(results) == 2
        assert all(r["status"] == "success" for r in results)


def test_publish_all_products(
    merchant: Merchant, product_event_ids: List[EventId]
) -> None:
    """Test publishing all products"""
    with patch.object(merchant._nostr_client, "publish_product") as mock_publish:
        mock_publish.side_effect = itertools.cycle(product_event_ids)

        results = json.loads(merchant.publish_all_products())
        assert len(results) == 3


def test_publish_all_stalls(merchant: Merchant, stall_event_ids: List[EventId]) -> None:
    """Test publishing all stalls"""
    with patch.object(merchant._nostr_client, "publish_stall") as mock_publish:
        mock_publish.side_effect = itertools.cycle(stall_event_ids)

        results = json.loads(merchant.publish_all_stalls())
        assert len(results) == 2


def test_error_handling(merchant: Merchant) -> None:
    """Test error handling in various scenarios"""
    result = json.loads(merchant.publish_product_by_name("NonExistentProduct"))
    assert result["status"] == "error"

    results = json.loads(merchant.publish_stall_by_name("NonExistentStall"))
    assert isinstance(results, list)
    assert results[0]["status"] == "error"

    results = json.loads(merchant.publish_products_by_stall_name("NonExistentStall"))
    assert isinstance(results, list)
    assert results[0]["status"] == "error"


def test_profile_operations(
    merchant: Merchant,
    profile_event_id: EventId,
    merchant_profile_name: str,
    merchant_profile_about: str,
) -> None:
    """Test profile-related operations"""
    profile_data = json.loads(merchant.get_profile())
    profile = json.loads(profile_data)  # Parse the nested JSON string
    assert profile["name"] == merchant_profile_name
    assert profile["about"] == merchant_profile_about

    with patch.object(merchant._nostr_client, "publish_profile") as mock_publish:
        mock_publish.return_value = profile_event_id
        result = json.loads(merchant.publish_profile())
        assert isinstance(result, dict)
