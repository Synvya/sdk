"""
This module contains the conftest file for the tests.
"""

from os import getenv
from pathlib import Path
from typing import List
from unittest.mock import Mock

import pytest
from _pytest.nodes import Item
from agno.agent import AgentKnowledge
from dotenv import load_dotenv

from synvya_sdk import (
    NostrKeys,
    Product,
    ProductShippingCost,
    Profile,
    Stall,
    StallShippingMethod,
    generate_keys,
)
from synvya_sdk.agno import BuyerTools, SellerTools

# Get directory where the script is located
script_dir = Path(__file__).parent
# Load .env from the script's directory
load_dotenv(script_dir / ".env")

# Load or generate keys for test profiles


def pytest_collection_modifyitems(items: List[Item]) -> None:
    """Define the desired execution order of test files"""
    # Define the desired execution order of test files
    ordered_files = [
        "tests/test_nostr_integration.py",
        "tests/test_nostr_mocked.py",
        "tests/test_merchant.py",
        "tests/test_buyer.py",
    ]

    # Create a dictionary mapping filenames to execution order
    order_map = {name: index for index, name in enumerate(ordered_files)}

    # Sort test items based on the order_map; default to a high value for unspecified files
    items.sort(key=lambda item: order_map.get(item.location[0], 100))


@pytest.fixture(scope="session", name="relay")
def relay_fixture() -> str:
    """Fixture providing the test relay"""
    return "wss://relay.damus.io"


###--- Merchant Fixtures ---###


@pytest.fixture(scope="session", name="merchant_keys")
def merchant_keys_fixture() -> NostrKeys:
    """Fixture providing the test merchant keys"""
    nsec = getenv("TEST_MERCHANT_KEY")
    if nsec is None:
        return generate_keys(env_var="TEST_MERCHANT_KEY", env_path=script_dir / ".env")
    return NostrKeys.from_private_key(nsec)


@pytest.fixture(scope="session", name="merchant_about")
def merchant_about_fixture() -> str:
    """Fixture providing the test profile about"""
    return "A merchant test profile"


@pytest.fixture(scope="session", name="merchant_banner")
def merchant_banner_fixture() -> str:
    """Fixture providing the test profile banner"""
    return "https://i.nostr.build/ENQ6OuMhoi2L17WD.png"


@pytest.fixture(scope="session", name="merchant_location")
def merchant_location_fixture() -> str:
    """Fixture providing the test location"""
    return "000000000"


@pytest.fixture(scope="session", name="merchant_name")
def merchant_name_fixture() -> str:
    """Fixture providing the test profile name"""
    return "Merchant Test Profile"


@pytest.fixture(scope="session", name="merchant_picture")
def merchant_picture_fixture() -> str:
    """Fixture providing the test profile picture"""
    return "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"


@pytest.fixture(scope="session", name="merchant_website")
def merchant_website_fixture() -> str:
    """Fixture providing the test profile website"""
    return "https://merchant.test"


@pytest.fixture(scope="session", name="merchant_profile")
def merchant_profile_fixture(
    merchant_keys: NostrKeys,
    merchant_about: str,
    merchant_banner: str,
    merchant_location: str,
    merchant_name: str,
    merchant_picture: str,
    merchant_website: str,
) -> Profile:
    """Fixture providing the test merchant profile"""
    profile = Profile(merchant_keys.get_public_key())
    profile.add_location(merchant_location)
    profile.set_about(merchant_about)
    profile.set_banner(merchant_banner)
    profile.set_name(merchant_name)
    profile.set_picture(merchant_picture)
    profile.set_website(merchant_website)
    return profile


###---  Buyer Fixtures ---###


@pytest.fixture(scope="session", name="buyer_keys")
def buyer_keys_fixture() -> NostrKeys:
    """Fixture providing the test buyer keys"""
    nsec = getenv("TEST_BUYER_KEY")
    if nsec is None:
        return generate_keys(env_var="TEST_BUYER_KEY", env_path=script_dir / ".env")
    return NostrKeys.from_private_key(nsec)


@pytest.fixture(scope="session", name="buyer_about")
def buyer_about_fixture() -> str:
    """Fixture providing the test profile about"""
    return "A buyer test profile"


@pytest.fixture(scope="session", name="buyer_banner")
def buyer_banner_fixture() -> str:
    """Fixture providing the test profile banner"""
    return "https://i.nostr.build/EiS8XFCROnSRr17o.png"


@pytest.fixture(scope="session", name="buyer_name")
def buyer_name_fixture() -> str:
    """Fixture providing the test profile name"""
    return "Buyer Test Profile"


@pytest.fixture(scope="session", name="buyer_picture")
def buyer_picture_fixture() -> str:
    """Fixture providing the test profile picture"""
    return "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"


@pytest.fixture(scope="session", name="buyer_website")
def buyer_website_fixture() -> str:
    """Fixture providing the test profile website"""
    return "https://buyer.test"


@pytest.fixture(scope="session", name="buyer_profile")
def buyer_profile_fixture(
    buyer_keys: NostrKeys,
    buyer_about: str,
    buyer_banner: str,
    buyer_name: str,
    buyer_picture: str,
    buyer_website: str,
) -> Profile:
    """Fixture providing the test merchant profile"""
    profile = Profile(buyer_keys.get_public_key())
    profile.set_about(buyer_about)
    profile.set_banner(buyer_banner)
    profile.set_name(buyer_name)
    profile.set_picture(buyer_picture)
    profile.set_website(buyer_website)
    return profile


@pytest.fixture(scope="session", name="profile_event_id")
def profile_event_id_fixture() -> str:
    """Fixture providing the test profile event id"""
    return "note1f8ew29sf9cdln2kf5c8eylkujgth6t06ae2vmt8k9ftjaljulmlset9qnj"


@pytest.fixture(scope="session", name="geohashs")
def geohashs_fixture() -> List[str]:
    """Fixture providing the test geohashs"""
    return ["000000000", "000000000"]


@pytest.fixture(scope="session", name="stall_shipping_methods")
def stall_shipping_methods_fixture() -> List[StallShippingMethod]:
    """Create stall shipping methods for testing"""
    return [
        StallShippingMethod(
            ssm_id="64be11rM",
            ssm_cost=10000,
            ssm_name="North America",
            ssm_regions=["Canada", "Mexico", "USA"],
        ),
        StallShippingMethod(
            ssm_id="d041HK7s",
            ssm_cost=20000,
            ssm_name="Rest of the World",
            ssm_regions=["All other countries"],
        ),
        StallShippingMethod(
            ssm_id="R8Gzz96K",
            ssm_cost=0,
            ssm_name="Worldwide",
            ssm_regions=["Worldwide"],
        ),
    ]


@pytest.fixture(scope="session", name="product_shipping_costs")
def product_shipping_costs_fixture() -> List[ProductShippingCost]:
    """Create product shipping costs for testing"""
    return [
        ProductShippingCost(psc_id="64be11rM", psc_cost=5000),
        ProductShippingCost(psc_id="d041HK7s", psc_cost=5000),
        ProductShippingCost(psc_id="R8Gzz96K", psc_cost=0),
    ]


@pytest.fixture(scope="session", name="stalls")
def stalls_fixture(
    stall_shipping_methods: List[StallShippingMethod], geohashs: List[str]
) -> List[Stall]:
    """Create Stall test fixtures"""
    return [
        Stall(
            id="212au4Pi",
            name="The Hardware Store",
            description="Your neighborhood hardware store, now available online.",
            currency="Sats",
            shipping=[stall_shipping_methods[0], stall_shipping_methods[1]],
            geohash=geohashs[0],
        ),
        Stall(
            id="212au4Ph",
            name="The Trade School",
            description="Educational videos to put all your hardware supplies to good use.",
            currency="Sats",
            shipping=[stall_shipping_methods[2]],
            geohash=geohashs[1],
        ),
    ]


@pytest.fixture(scope="session", name="stall_event_ids")
def stall_event_ids_fixture() -> List[str]:
    """Fixture providing valid but dummy hex test stall event ids"""
    return [
        "c12fed92c3dd928fcce4a5d0a5ec608aa52687f4ac45fad6ef1b4895c19fec75",
        "ecc04d51f124598abb7bd6830e169dbd4d97aef3bfc19a20ba07b99db709b893",
    ]


@pytest.fixture(scope="session", name="products")
def products_fixture(
    product_shipping_costs: List[ProductShippingCost],
) -> List[Product]:
    """Create Product test fixtures"""
    return [
        Product(
            id="bcf00Rx7",
            stall_id="212au4Pi",
            name="Wrench",
            description="The perfect tool for a $5 wrench attack.",
            images=["https://i.nostr.build/BddyYILz0rjv1wEY.png"],
            currency="Sats",
            price=5000,
            quantity=100,
            shipping=[product_shipping_costs[0], product_shipping_costs[1]],
            specs=[["length", "10cm"], ["material", "steel"]],
            categories=["hardware", "tools"],
        ),
        Product(
            id="bcf00Rx8",
            stall_id="212au4Pi",
            name="Shovel",
            description="Dig yourself into a hole like never before",
            images=["https://i.nostr.build/psL0ZtN4FZcmeiIh.png"],
            currency="Sats",
            price=10000,
            quantity=10,
            shipping=[product_shipping_costs[0], product_shipping_costs[1]],
            specs=[["length", "100 cm"], ["material", "steel"]],
            categories=["hardware", "tools"],
        ),
        Product(
            id="ccf00Rx1",
            stall_id="212au4Ph",
            name="Shovel 101",
            description="How to dig your own grave",
            images=["https://i.nostr.build/psL0ZtN4FZcmeiIh.png"],
            currency="Sats",
            price=1000,
            quantity=1000,
            shipping=[product_shipping_costs[2]],
            specs=[["type", "online"], ["media", "video"]],
            categories=["education", "hardware tools"],
        ),
    ]


@pytest.fixture(scope="session", name="product_event_ids")
def product_event_ids_fixture() -> List[str]:
    """Fixture providing  valid but dummy hex test product event ids"""
    return [
        "d1441f3532a44772fba7c57eb7c71c94c3971246722ae6e372cf50c198af784a",
        "b6a81ca6cbd5fa59e564208796a76af670a7a402ec0bb4621c999688ed10e43e",
        "dc25ae17347de75763c7462d7b7e26011167b05a60c425e3cf9aecea753930e6",
    ]


@pytest.fixture(scope="session", name="seller_tools")
def seller_tools_fixture(
    relay: str,
    merchant_keys: NostrKeys,
    stalls: List[Stall],
    products: List[Product],
) -> SellerTools:
    """Create a Seller instance for testing"""
    return SellerTools(relay, merchant_keys.get_private_key(), stalls, products)


@pytest.fixture(scope="session", name="mock_knowledge_base")
def mock_knowledge_base_fixture() -> Mock:
    """Fixture to return a mocked AgentKnowledge object."""
    return Mock(spec=AgentKnowledge)


@pytest.fixture(scope="session", name="buyer_tools")
def buyer_tools_fixture(
    mock_knowledge_base: Mock,
    relay: str,
    buyer_keys: NostrKeys,
    merchant_profile: Profile,
) -> BuyerTools:
    """Create a Buyer instance for testing"""
    buyer_tools = BuyerTools(mock_knowledge_base, relay, buyer_keys.get_private_key())
    buyer_tools.sellers = {merchant_profile}
    return buyer_tools
