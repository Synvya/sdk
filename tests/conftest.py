"""
This module contains the conftest file for the tests.
"""

import functools
from os import getenv
from pathlib import Path
from typing import List
from unittest.mock import Mock

import pytest
from _pytest.nodes import Item
from agno.agent import AgentKnowledge
from dotenv import load_dotenv

from agentstr import (
    AgentProfile,
    BuyerTools,
    EventId,
    Keys,
    Kind,
    MerchantProduct,
    MerchantStall,
    MerchantTools,
    NostrProfile,
    ShippingCost,
    ShippingMethod,
    Timestamp,
    generate_and_save_keys,
)

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


@pytest.fixture(scope="session", name="merchant_keys")
@functools.lru_cache(maxsize=1)
def merchant_keys_fixture() -> Keys:
    """Cache keys for the merchant profile to prevent unnecessary generation."""
    nsec = getenv("TEST_MERCHANT_KEY")
    return (
        Keys.parse(nsec)
        if nsec
        else generate_and_save_keys(
            env_var="TEST_MERCHANT_KEY", env_path=script_dir / ".env"
        )
    )


@pytest.fixture(scope="session", name="buyer_keys")
@functools.lru_cache(maxsize=1)
def buyer_keys_fixture() -> Keys:
    """Cache keys for the buyer profile."""
    nsec = getenv("TEST_BUYER_KEY")
    return (
        Keys.parse(nsec)
        if nsec
        else generate_and_save_keys(
            env_var="TEST_BUYER_KEY", env_path=script_dir / ".env"
        )
    )


@pytest.fixture(scope="session", name="relay")
def relay_fixture() -> str:
    """Fixture providing the test relay"""
    return "wss://relay.damus.io"


@pytest.fixture(scope="session", name="merchant_location")
def merchant_location_fixture() -> str:
    """Fixture providing the test location"""
    return "Snoqualmie, WA"


@pytest.fixture(scope="session", name="merchant_profile_name")
def merchant_profile_name_fixture() -> str:
    """Fixture providing the test profile name"""
    return "Merchant Test Profile"


@pytest.fixture(scope="session", name="buyer_profile_name")
def buyer_profile_name_fixture() -> str:
    """Fixture providing the test profile name"""
    return "Buyer Test Profile"


@pytest.fixture(scope="session", name="merchant_profile_about")
def merchant_profile_about_fixture() -> str:
    """Fixture providing the test profile about"""
    return "A merchant test profile"


@pytest.fixture(scope="session", name="buyer_profile_about")
def buyer_profile_about_fixture() -> str:
    """Fixture providing the test profile about"""
    return "A buyer test profile"


@pytest.fixture(scope="session", name="merchant_profile_picture")
def merchant_profile_picture_fixture() -> str:
    """Fixture providing the test profile picture"""
    return "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"


@pytest.fixture(scope="session", name="buyer_profile_picture")
def buyer_profile_picture_fixture() -> str:
    """Fixture providing the test profile picture"""
    return "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"


@pytest.fixture(scope="session", name="profile_event_id")
def profile_event_id_fixture(merchant_keys: Keys) -> EventId:
    """Fixture providing the test profile event id"""
    event_id = EventId(
        public_key=merchant_keys.public_key(),
        created_at=Timestamp.from_secs(1739580690),
        kind=Kind(0),
        tags=[],
        content=(
            '{"name":"Merchant Test Profile",'
            '"about":"A merchant test profile",'
            '"picture":"https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"}'
        ),
    )
    return event_id


@pytest.fixture(scope="session", name="geohashs")
def geohashs_fixture() -> List[str]:
    """Fixture providing the test geohashs"""
    return ["000000000", "000000000"]


@pytest.fixture(scope="session", name="merchant_profile")
def merchant_profile_fixture(
    merchant_keys: Keys,
    merchant_profile_name: str,
    merchant_profile_about: str,
    merchant_profile_picture: str,
) -> AgentProfile:
    """Fixture providing the test merchant profile"""
    profile = AgentProfile(keys=merchant_keys)
    profile.set_name(merchant_profile_name)
    profile.set_about(merchant_profile_about)
    profile.set_picture(merchant_profile_picture)
    return profile


@pytest.fixture(scope="session", name="seller_nostr_profile")
def seller_nostr_profile_fixture(
    merchant_keys: Keys, merchant_profile: AgentProfile, geohashs: List[str]
) -> NostrProfile:
    """Create a NostrProfile instance for tests"""
    nostr_profile = NostrProfile(merchant_keys.public_key())
    nostr_profile.set_name(merchant_profile.get_name())
    nostr_profile.set_about(merchant_profile.get_about())
    nostr_profile.set_picture(merchant_profile.get_picture())
    nostr_profile.add_location(geohashs[0])
    return nostr_profile


@pytest.fixture(scope="session", name="buyer_profile")
def buyer_profile_fixture(
    buyer_keys: Keys,
    buyer_profile_name: str,
    buyer_profile_about: str,
    buyer_profile_picture: str,
) -> AgentProfile:
    """Fixture providing the test buyer profile"""
    profile = AgentProfile(keys=buyer_keys)
    profile.set_name(buyer_profile_name)
    profile.set_about(buyer_profile_about)
    profile.set_picture(buyer_profile_picture)
    return profile


@pytest.fixture(scope="session", name="shipping_methods")
def shipping_methods_fixture() -> List[ShippingMethod]:
    """Create shipping methods for testing"""
    method1 = (
        ShippingMethod(id="64be11rM", cost=10000)
        .name("North America")
        .regions(["Canada", "Mexico", "USA"])
    )

    method2 = (
        ShippingMethod(id="d041HK7s", cost=20000)
        .name("Rest of the World")
        .regions(["All other countries"])
    )

    method3 = (
        ShippingMethod(id="R8Gzz96K", cost=0).name("Worldwide").regions(["Worldwide"])
    )

    return [method1, method2, method3]


@pytest.fixture(scope="session", name="shipping_costs")
def shipping_costs_fixture() -> List[ShippingCost]:
    """Create shipping costs for testing"""
    return [
        ShippingCost(id="64be11rM", cost=5000),
        ShippingCost(id="d041HK7s", cost=5000),
        ShippingCost(id="R8Gzz96K", cost=0),
    ]


@pytest.fixture(scope="session", name="merchant_stalls")
def merchant_stalls_fixture(
    shipping_methods: List[ShippingMethod], geohashs: List[str]
) -> List[MerchantStall]:
    """Create MerchantStall test fixtures"""
    return [
        MerchantStall(
            id="212au4Pi",
            name="The Hardware Store",
            description="Your neighborhood hardware store, now available online.",
            currency="Sats",
            shipping=[shipping_methods[0], shipping_methods[1]],
            geohash=geohashs[0],
        ),
        MerchantStall(
            id="212au4Ph",
            name="The Trade School",
            description="Educational videos to put all your hardware supplies to good use.",
            currency="Sats",
            shipping=[shipping_methods[2]],
            geohash=geohashs[1],
        ),
    ]


@pytest.fixture(scope="session", name="merchant_products")
def merchant_products_fixture(
    shipping_costs: List[ShippingCost],
) -> List[MerchantProduct]:
    """Create MerchantProduct test fixtures"""
    return [
        MerchantProduct(
            id="bcf00Rx7",
            stall_id="212au4Pi",
            name="Wrench",
            description="The perfect tool for a $5 wrench attack.",
            images=["https://i.nostr.build/BddyYILz0rjv1wEY.png"],
            currency="Sats",
            price=5000,
            quantity=100,
            shipping=[shipping_costs[0], shipping_costs[1]],
            specs=[["length", "10cm"], ["material", "steel"]],
            categories=["hardware", "tools"],
        ),
        MerchantProduct(
            id="bcf00Rx8",
            stall_id="212au4Pi",
            name="Shovel",
            description="Dig yourself into a hole like never before",
            images=["https://i.nostr.build/psL0ZtN4FZcmeiIh.png"],
            currency="Sats",
            price=10000,
            quantity=10,
            shipping=[shipping_costs[0], shipping_costs[1]],
            specs=[["length", "100 cm"], ["material", "steel"]],
            categories=["hardware", "tools"],
        ),
        MerchantProduct(
            id="ccf00Rx1",
            stall_id="212au4Ph",
            name="Shovel 101",
            description="How to dig your own grave",
            images=["https://i.nostr.build/psL0ZtN4FZcmeiIh.png"],
            currency="Sats",
            price=1000,
            quantity=1000,
            shipping=[shipping_costs[2]],
            specs=[["type", "online"], ["media", "video"]],
            categories=["education", "hardware tools"],
        ),
    ]


@pytest.fixture(scope="session", name="merchant_tools")
def merchant_tools_fixture(
    merchant_profile: AgentProfile,
    relay: str,
    merchant_stalls: List[MerchantStall],
    merchant_products: List[MerchantProduct],
) -> MerchantTools:
    """Create a Merchant instance for testing"""
    return MerchantTools(merchant_profile, relay, merchant_stalls, merchant_products)


@pytest.fixture(scope="session", name="mock_knowledge_base")
def mock_knowledge_base_fixture() -> Mock:
    """Fixture to return a mocked AgentKnowledge object."""
    return Mock(spec=AgentKnowledge)


@pytest.fixture(scope="session", name="buyer_tools")
def buyer_tools_fixture(
    mock_knowledge_base: Mock,
    buyer_profile: AgentProfile,
    relay: str,
    seller_nostr_profile: NostrProfile,
) -> BuyerTools:
    """Create a Buyer instance for testing"""
    buyer_tools = BuyerTools(mock_knowledge_base, buyer_profile, relay)
    buyer_tools.sellers = {seller_nostr_profile}
    return buyer_tools


@pytest.fixture(scope="session", name="product_event_ids")
def product_event_ids_fixture() -> List[EventId]:
    """Fixture providing  valid but dummy hex test product event ids"""
    return [
        EventId.parse(
            "d1441f3532a44772fba7c57eb7c71c94c3971246722ae6e372cf50c198af784a"
        ),
        EventId.parse(
            "b6a81ca6cbd5fa59e564208796a76af670a7a402ec0bb4621c999688ed10e43e"
        ),
        EventId.parse(
            "dc25ae17347de75763c7462d7b7e26011167b05a60c425e3cf9aecea753930e6"
        ),
    ]


@pytest.fixture(scope="session", name="stall_event_ids")
def stall_event_ids_fixture() -> List[EventId]:
    """Fixture providing valid but dummy hex test stall event ids"""
    return [
        EventId.parse(
            "c12fed92c3dd928fcce4a5d0a5ec608aa52687f4ac45fad6ef1b4895c19fec75"
        ),
        EventId.parse(
            "ecc04d51f124598abb7bd6830e169dbd4d97aef3bfc19a20ba07b99db709b893"
        ),
    ]
