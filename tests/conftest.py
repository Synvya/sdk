from os import getenv
from pathlib import Path
from typing import Any, List

import pytest
from _pytest.config import Config
from _pytest.main import Session
from _pytest.nodes import Item
from dotenv import load_dotenv

from agentstr.buyer import BuyerTools
from agentstr.merchant import MerchantTools
from agentstr.models import AgentProfile, MerchantProduct, MerchantStall, NostrProfile
from agentstr.nostr import (
    EventId,
    Keys,
    Kind,
    NostrClient,
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


def pytest_collection_modifyitems(
    session: Session, config: Config, items: List[Item]
) -> None:
    """Define the desired execution order of test files"""
    # Define the desired execution order of test files
    ordered_files = [
        "tests/test_nostr.py",
        "tests/test_merchant.py",
        "tests/test_buyer.py",
    ]

    # Create a dictionary mapping filenames to execution order
    order_map = {name: index for index, name in enumerate(ordered_files)}

    # Sort test items based on the order_map; default to a high value for unspecified files
    items.sort(key=lambda item: order_map.get(item.location[0], 100))


@pytest.fixture
def merchant_keys() -> Keys:
    nsec = getenv("TEST_MERCHANT_KEY")
    if nsec is None:
        merchant_keys = generate_and_save_keys(
            env_var="TEST_MERCHANT_KEY", env_path=script_dir / ".env"
        )
    else:
        merchant_keys = Keys.parse(nsec)
    return merchant_keys


@pytest.fixture
def buyer_keys() -> Keys:
    nsec = getenv("TEST_BUYER_KEY")
    if nsec is None:
        buyer_keys = generate_and_save_keys(
            env_var="TEST_BUYER_KEY", env_path=script_dir / ".env"
        )
    else:
        buyer_keys = Keys.parse(nsec)
    return buyer_keys


@pytest.fixture
def relay() -> str:
    """Fixture providing the test relay"""
    return "wss://relay.damus.io"


@pytest.fixture
def merchant_location() -> str:
    """Fixture providing the test location"""
    return "Snoqualmie, WA"


@pytest.fixture
def merchant_profile_name() -> str:
    """Fixture providing the test profile name"""
    return "Merchant Test Profile"


@pytest.fixture
def buyer_profile_name() -> str:
    """Fixture providing the test profile name"""
    return "Buyer Test Profile"


@pytest.fixture
def merchant_profile_about() -> str:
    """Fixture providing the test profile about"""
    return "A merchant test profile"


@pytest.fixture
def buyer_profile_about() -> str:
    """Fixture providing the test profile about"""
    return "A buyer test profile"


@pytest.fixture
def merchant_profile_picture() -> str:
    """Fixture providing the test profile picture"""
    return "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"


@pytest.fixture
def buyer_profile_picture() -> str:
    """Fixture providing the test profile picture"""
    return "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"


@pytest.fixture
def profile_event_id(merchant_keys: Keys) -> EventId:
    event_id = EventId(
        public_key=merchant_keys.public_key(),
        created_at=Timestamp.from_secs(1739580690),
        kind=Kind(0),
        tags=[],
        content='{"name":"Merchant Test Profile","about":"A merchant test profile","picture":"https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"}',
    )
    return event_id


@pytest.fixture
def seller_nostr_profile(merchant_keys: Keys) -> NostrProfile:
    """Create a NostrProfile instance for tests"""
    return NostrProfile(merchant_keys.public_key())


@pytest.fixture
def merchant_profile(
    merchant_keys: Keys,
    merchant_profile_name: str,
    merchant_profile_about: str,
    merchant_profile_picture: str,
) -> AgentProfile:
    profile = AgentProfile(keys=merchant_keys)
    profile.set_name(merchant_profile_name)
    profile.set_about(merchant_profile_about)
    profile.set_picture(merchant_profile_picture)
    return profile


@pytest.fixture
def buyer_profile(
    buyer_keys: Keys,
    buyer_profile_name: str,
    buyer_profile_about: str,
    buyer_profile_picture: str,
) -> AgentProfile:
    profile = AgentProfile(keys=buyer_keys)
    profile.set_name(buyer_profile_name)
    profile.set_about(buyer_profile_about)
    profile.set_picture(buyer_profile_picture)
    return profile


@pytest.fixture
def nostr_client(relay: str, merchant_keys: Keys) -> NostrClient:
    """Fixture providing a NostrClient instance"""
    nostr_client = NostrClient(relay, merchant_keys.secret_key().to_bech32())
    return nostr_client


@pytest.fixture
def shipping_methods() -> List[ShippingMethod]:
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


@pytest.fixture
def shipping_costs() -> List[ShippingCost]:
    """Create shipping costs for testing"""
    return [
        ShippingCost(id="64be11rM", cost=5000),
        ShippingCost(id="d041HK7s", cost=5000),
        ShippingCost(id="R8Gzz96K", cost=0),
    ]


@pytest.fixture
def geohashs() -> List[str]:
    """Fixture providing the test geohashs"""
    return ["C23Q7U36W", "C23Q7U36W"]


@pytest.fixture
def merchant_stalls(
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


@pytest.fixture
def merchant_products(shipping_costs: List[ShippingCost]) -> List[MerchantProduct]:
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
            specs=None,
            categories=None,
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
        ),
    ]


@pytest.fixture
def merchant_tools(
    merchant_profile: AgentProfile,
    relay: str,
    merchant_stalls: List[MerchantStall],
    merchant_products: List[MerchantProduct],
) -> MerchantTools:
    """Create a Merchant instance for testing"""
    return MerchantTools(merchant_profile, relay, merchant_stalls, merchant_products)


@pytest.fixture
def buyer_tools(
    buyer_profile: AgentProfile,
    relay: str,
) -> BuyerTools:
    """Create a Buyer instance for testing"""
    buyer_tools = BuyerTools(buyer_profile, relay)
    buyer_tools.get_sellers()  # gets a new list since the BuyerTools instance is new
    return buyer_tools


@pytest.fixture
def product_event_ids() -> List[EventId]:
    # provide valid but dummy hex event id strings
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


@pytest.fixture
def stall_event_ids() -> List[EventId]:
    # provide valid but dummy hex event id strings
    return [
        EventId.parse(
            "c12fed92c3dd928fcce4a5d0a5ec608aa52687f4ac45fad6ef1b4895c19fec75"
        ),
        EventId.parse(
            "ecc04d51f124598abb7bd6830e169dbd4d97aef3bfc19a20ba07b99db709b893"
        ),
    ]
