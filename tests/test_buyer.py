import json

from agentstr.buyer import BuyerTools
from agentstr.models import AgentProfile, NostrProfile
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
    buyer_tools: BuyerTools, merchant_keys: Keys
) -> None:
    result = buyer_tools.find_seller_by_public_key(
        merchant_keys.public_key().to_bech32()
    )
    assert result is not None
    assert merchant_keys.public_key().to_bech32() in result


def test_get_seller_collections(
    buyer_tools: BuyerTools, seller_nostr_profile: NostrProfile
) -> None:
    result = buyer_tools.get_seller_collections(seller_nostr_profile.get_public_key())
    assert result is not None


def test_get_seller_products(
    buyer_tools: BuyerTools, seller_nostr_profile: NostrProfile
) -> None:
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
