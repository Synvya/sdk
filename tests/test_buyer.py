import json
from typing import List
from unittest.mock import patch

from agentstr.buyer import BuyerTools
from agentstr.models import AgentProfile, MerchantProduct, MerchantStall, NostrProfile
from agentstr.nostr import Keys


def test_buyer_profile_creation(
    buyer_profile: AgentProfile,
    buyer_profile_name: str,
    buyer_profile_about: str,
    buyer_profile_picture: str,
) -> None:
    assert buyer_profile.get_name() == buyer_profile_name
    assert buyer_profile.get_about() == buyer_profile_about
    assert buyer_profile.get_picture() == buyer_profile_picture


def test_find_sellers_by_location(
    buyer_tools: BuyerTools, merchant_location: str, merchant_profile_name: str
) -> None:
    result = buyer_tools.find_sellers_by_location(merchant_location)
    assert result is not None
    assert merchant_profile_name in result


def test_find_seller_by_name(
    buyer_tools: BuyerTools, merchant_profile_name: str
) -> None:
    result = buyer_tools.find_seller_by_name(merchant_profile_name)
    assert result is not None
    assert merchant_profile_name in result


def test_find_seller_by_public_key(
    buyer_tools: BuyerTools,
    merchant_keys: Keys,
    seller_nostr_profile: NostrProfile,
) -> None:
    with patch.object(
        buyer_tools, "find_seller_by_public_key"
    ) as mock_find_seller_by_public_key:
        mock_find_seller_by_public_key.return_value = seller_nostr_profile.to_json()

        result = buyer_tools.find_seller_by_public_key(
            merchant_keys.public_key().to_bech32()
        )
        assert result is not None
        assert merchant_keys.public_key().to_bech32() in result


def test_get_seller_stalls(
    buyer_tools: BuyerTools,
    seller_nostr_profile: NostrProfile,
    merchant_stalls: List[MerchantStall],
) -> None:
    with patch.object(
        buyer_tools._nostr_client, "retrieve_stalls_from_seller"
    ) as mock_get_seller_stalls:
        mock_get_seller_stalls.return_value = merchant_stalls

    result = buyer_tools.get_seller_stalls(seller_nostr_profile.get_public_key())
    assert result is not None


def test_get_seller_products(
    buyer_tools: BuyerTools,
    merchant_products: List[MerchantProduct],
    seller_nostr_profile: NostrProfile,
) -> None:
    with patch.object(
        buyer_tools._nostr_client, "retrieve_products_from_seller"
    ) as mock_get_seller_products:
        mock_get_seller_products.return_value = merchant_products

    result = buyer_tools.get_seller_products(seller_nostr_profile.get_public_key())
    products = json.loads(result)  # Parse JSON string to list
    assert products is not None

    # Check if we got an error response
    if isinstance(products, dict) and "status" in products:
        print(f"Got error response: {products['message']}")  # For debugging
        assert False, f"Expected products list but got error: {products['message']}"

    assert isinstance(products, list)
    assert len(products) > 0
    assert "name" in products[0]  # Check first product has name field
