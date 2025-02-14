import json
from os import getenv
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from dotenv import load_dotenv

from agentstr.buyer import Buyer
from agentstr.models import AgentProfile, MerchantProduct, NostrProfile
from agentstr.nostr import Keys, PublicKey, generate_and_save_keys

# Environment variables
ENV_RELAY = "RELAY"
DEFAULT_RELAY = "wss://relay.damus.io"
ENV_KEY = "NSEC_TEST_KEY"

# Buyer profile constants
NAME = "BusinessTestName"
DESCRIPTION = "I'm in the business of doing business tests."
PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"
DISPLAY_NAME = "Buyer Agent for Business Test Name Inc."


# Load environment variables
load_dotenv()

SELLER_NAME = "Test Profile"
SELLER_PUBLIC_KEY = "npub176r83h7rdsppmeqj0uyvzav0c69ynusmwgat4rn80jzmv9z4kg4sytqqx7"
LOCATION = "Snoqualmie, WA"


@pytest.fixture
def keys() -> Keys:
    # Load or generate keys
    nsec = getenv(ENV_KEY)

    if nsec is None:
        keys = generate_and_save_keys(env_var=ENV_KEY)
    else:
        keys = Keys.parse(nsec)
    return keys


@pytest.fixture
def relay() -> str:
    # Load or use default relay
    relay = getenv(ENV_RELAY)
    if relay is None:
        relay = DEFAULT_RELAY
    return relay


@pytest.fixture
def buyer_profile(keys: Keys) -> AgentProfile:
    # Initialize a buyer profile using the create classmethod
    buyer_profile = AgentProfile(keys=keys)
    buyer_profile.set_name(NAME)
    buyer_profile.set_about(DESCRIPTION)
    buyer_profile.set_display_name(DISPLAY_NAME)
    buyer_profile.set_picture(PICTURE)
    return buyer_profile


@pytest.fixture
def nostr_profile() -> NostrProfile:
    """Create a NostrProfile instance for tests"""
    return NostrProfile(PublicKey.parse(SELLER_PUBLIC_KEY))


@pytest.fixture
def buyer(buyer_profile: AgentProfile, relay: str) -> Buyer:
    """
    A fixture that returns a Buyer instance with a new list of sellers.
    """
    buyer = Buyer(buyer_profile, relay)
    buyer.get_sellers()  # gets a new list since the Buyer instance is new
    return buyer


def test_buyer_profile_creation(buyer_profile: AgentProfile) -> None:
    assert buyer_profile.get_name() == NAME
    assert buyer_profile.get_about() == DESCRIPTION
    assert buyer_profile.get_display_name() == DISPLAY_NAME
    assert buyer_profile.get_picture() == PICTURE


def test_find_sellers_by_location(buyer: Buyer) -> None:
    result = buyer.find_sellers_by_location(LOCATION)
    assert result is not None
    assert SELLER_NAME in result


def test_find_seller_by_name(buyer: Buyer) -> None:
    result = buyer.find_seller_by_name(SELLER_NAME)
    assert result is not None
    assert SELLER_NAME in result


def test_find_seller_by_public_key(buyer: Buyer) -> None:
    result = buyer.find_seller_by_public_key(SELLER_PUBLIC_KEY)
    assert result is not None
    assert SELLER_PUBLIC_KEY in result


def test_get_seller_collections(buyer: Buyer, nostr_profile: NostrProfile) -> None:
    result = buyer.get_seller_collections(SELLER_PUBLIC_KEY)
    assert result is not None


def test_get_seller_products(buyer: Buyer, nostr_profile: NostrProfile) -> None:
    result = buyer.get_seller_products(SELLER_PUBLIC_KEY)
    products = json.loads(result)  # Parse JSON string to list
    assert products is not None

    # Check if we got an error response
    if isinstance(products, dict) and "status" in products:
        print(f"Got error response: {products['message']}")  # For debugging
        assert False, f"Expected products list but got error: {products['message']}"

    assert isinstance(products, list)
    assert len(products) > 0
    assert "name" in products[0]  # Check first product has name field
