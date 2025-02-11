import itertools
import json
from os import getenv
from typing import List, Literal
from unittest.mock import Mock, patch

import pytest
from dotenv import load_dotenv

from agentstr.merchant import (
    EventId,
    Merchant,
    MerchantProduct,
    MerchantStall,
    NostrClient,
    ProductData,
    Profile,
    ShippingCost,
    ShippingMethod,
    StallData,
)
from agentstr.nostr import (
    Event,
    EventBuilder,
    Keys,
    Kind,
    Metadata,
    PublicKey,
    Timestamp,
)

load_dotenv()

RELAY = "wss://relay.damus.io"

# --*-- Merchant info
MERCHANT_NAME = "Merchant 1"
MERCHANT_DESCRIPTION = "Selling products peer to peer"
MERCHANT_PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"

# --*-- Stall info
STALL_1_NAME = "The Hardware Store"
STALL_1_ID = "212au4Pi"  # "212a26qV"
STALL_1_DESCRIPTION = "Your neighborhood hardware store, now available online."
STALL_1_CURRENCY = "Sats"

STALL_2_NAME = "The Trade School"
STALL_2_ID = "c8762EFD"
STALL_2_DESCRIPTION = (
    "Educational videos to put all your hardware supplies to good use."
)
STALL_2_CURRENCY = "Sats"

# --*-- Shipping info
SHIPPING_ZONE_1_NAME = "North America"
SHIPPING_ZONE_1_ID = "64be11rM"
SHIPPING_ZONE_1_REGIONS = ["Canada", "Mexico", "USA"]

SHIPPING_ZONE_2_NAME = "Rest of the World"
SHIPPING_ZONE_2_ID = "d041HK7s"
SHIPPING_ZONE_2_REGIONS = ["All other countries"]

SHIPPING_ZONE_3_NAME = "Worldwide"
SHIPPING_ZONE_3_ID = "R8Gzz96K"
SHIPPING_ZONE_3_REGIONS = ["Worldwide"]

# --*-- Product info
PRODUCT_1_NAME = "Wrench"
PRODUCT_1_ID = "bcf00Rx7"
PRODUCT_1_DESCRIPTION = "The perfect tool for a $5 wrench attack."
PRODUCT_1_IMAGES = ["https://i.nostr.build/BddyYILz0rjv1wEY.png"]
PRODUCT_1_CURRENCY = STALL_1_CURRENCY
PRODUCT_1_PRICE = 5000
PRODUCT_1_QUANTITY = 100

PRODUCT_2_NAME = "Shovel"
PRODUCT_2_ID = "bcf00Rx8"
PRODUCT_2_DESCRIPTION = "Dig holes like never before"
PRODUCT_2_IMAGES = ["https://i.nostr.build/psL0ZtN4FZcmeiIh.png"]
PRODUCT_2_CURRENCY = STALL_1_CURRENCY
PRODUCT_2_PRICE = 10000
PRODUCT_2_QUANTITY = 10

PRODUCT_3_NAME = "Shovel 101"
PRODUCT_3_ID = "ccf00Rx1"
PRODUCT_3_DESCRIPTION = "How to dig your own grave"
PRODUCT_3_IMAGES = ["https://i.nostr.build/psL0ZtN4FZcmeiIh.png"]
PRODUCT_3_CURRENCY = STALL_2_CURRENCY
PRODUCT_3_PRICE = 1000
PRODUCT_3_QUANTITY = 1000


@pytest.fixture
def relay() -> str:
    return RELAY


@pytest.fixture
def profile_event_id() -> EventId:
    event_id = EventId(
        public_key=PublicKey.parse(
            "bbd4a62e5612c5430f745bd116bac79fd186d14c1b859a02d5920f749c8a453b"
        ),
        created_at=Timestamp.from_secs(1737436574),
        kind=Kind(0),
        tags=[],
        content='{"name":"Synvya Inc","about":"Agentic communications","picture":"https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"}',
    )
    return event_id


@pytest.fixture
def merchant_profile() -> Profile:
    nsec = getenv("NSEC_KEY")
    profile = Profile(MERCHANT_NAME, MERCHANT_DESCRIPTION, MERCHANT_PICTURE, nsec)
    return profile


@pytest.fixture
def nostr_client() -> NostrClient:
    nsec = getenv("NSEC_KEY")
    return NostrClient(RELAY, nsec)


@pytest.fixture
def shipping_methods() -> List[ShippingMethod]:
    return [
        ShippingMethod(id=SHIPPING_ZONE_1_ID, cost=10000)
        .name(SHIPPING_ZONE_1_NAME)
        .regions(SHIPPING_ZONE_1_REGIONS),
        ShippingMethod(id=SHIPPING_ZONE_2_ID, cost=10000)
        .name(SHIPPING_ZONE_2_NAME)
        .regions(SHIPPING_ZONE_2_REGIONS),
        ShippingMethod(id=SHIPPING_ZONE_3_ID, cost=10000)
        .name(SHIPPING_ZONE_3_NAME)
        .regions(SHIPPING_ZONE_3_REGIONS),
    ]


@pytest.fixture
def shipping_costs() -> List[ShippingCost]:
    return [
        ShippingCost(id=SHIPPING_ZONE_1_ID, cost=5000),
        ShippingCost(id=SHIPPING_ZONE_2_ID, cost=5000),
        ShippingCost(id=SHIPPING_ZONE_3_ID, cost=0),
    ]


@pytest.fixture
def merchant_stalls(shipping_methods: List[ShippingMethod]) -> List[MerchantStall]:
    """Create MerchantStall test fixtures"""
    return [
        MerchantStall(
            id=STALL_1_ID,
            name=STALL_1_NAME,
            description=STALL_1_DESCRIPTION,
            currency=STALL_1_CURRENCY,
            shipping=[shipping_methods[0], shipping_methods[1]],
        ),
        MerchantStall(
            id=STALL_2_ID,
            name=STALL_2_NAME,
            description=STALL_2_DESCRIPTION,
            currency=STALL_2_CURRENCY,
            shipping=[shipping_methods[2]],
        ),
    ]


@pytest.fixture
def merchant_products(shipping_costs: List[ShippingCost]) -> List[MerchantProduct]:
    """Create MerchantProduct test fixtures"""
    return [
        MerchantProduct(
            id=PRODUCT_1_ID,
            stall_id=STALL_1_ID,
            name=PRODUCT_1_NAME,
            description=PRODUCT_1_DESCRIPTION,
            images=PRODUCT_1_IMAGES,
            currency=PRODUCT_1_CURRENCY,
            price=PRODUCT_1_PRICE,
            quantity=PRODUCT_1_QUANTITY,
            shipping=[shipping_costs[0], shipping_costs[1]],
        ),
        MerchantProduct(
            id=PRODUCT_2_ID,
            stall_id=STALL_1_ID,
            name=PRODUCT_2_NAME,
            description=PRODUCT_2_DESCRIPTION,
            images=PRODUCT_2_IMAGES,
            currency=PRODUCT_2_CURRENCY,
            price=PRODUCT_2_PRICE,
            quantity=PRODUCT_2_QUANTITY,
            shipping=[shipping_costs[0], shipping_costs[1]],
        ),
        MerchantProduct(
            id=PRODUCT_3_ID,
            stall_id=STALL_2_ID,
            name=PRODUCT_3_NAME,
            description=PRODUCT_3_DESCRIPTION,
            images=PRODUCT_3_IMAGES,
            currency=PRODUCT_3_CURRENCY,
            price=PRODUCT_3_PRICE,
            quantity=PRODUCT_3_QUANTITY,
            shipping=[shipping_costs[2]],
        ),
    ]


@pytest.fixture
def merchant(
    merchant_profile: Profile,
    relay: str,
    merchant_stalls: List[MerchantStall],
    merchant_products: List[MerchantProduct],
) -> Merchant:
    """Create a Merchant instance for testing"""
    return Merchant(merchant_profile, relay, merchant_stalls, merchant_products)


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


def test_merchant_initialization(merchant: Merchant) -> None:
    """Test merchant initialization"""
    assert merchant.merchant_profile is not None
    assert merchant.relay == RELAY
    assert len(merchant.product_db) == 3
    assert len(merchant.stall_db) == 2

    products = json.loads(merchant.get_products())
    assert len(products) == 3
    assert products[0]["name"] == PRODUCT_1_NAME

    stalls = json.loads(merchant.get_stalls())
    assert len(stalls) == 2
    assert stalls[0]["name"] == STALL_1_NAME


def test_publish_product_by_name(
    merchant: Merchant, product_event_ids: List[EventId]
) -> None:
    """Test publishing a product by name"""
    with patch.object(merchant._nostr_client, "publish_product") as mock_publish:
        mock_publish.return_value = product_event_ids[0]

        result = json.loads(merchant.publish_product_by_name(PRODUCT_1_NAME))
        assert result["status"] == "success"
        assert result["product_name"] == PRODUCT_1_NAME

        result = json.loads(
            merchant.publish_product_by_name(json.dumps({"name": PRODUCT_1_NAME}))
        )
        assert result["status"] == "success"
        assert result["product_name"] == PRODUCT_1_NAME


def test_publish_stall_by_name(
    merchant: Merchant, stall_event_ids: List[EventId]
) -> None:
    """Test publishing a stall by name"""
    with patch.object(merchant._nostr_client, "publish_stall") as mock_publish:
        mock_publish.return_value = stall_event_ids[0]

        result = json.loads(merchant.publish_stall_by_name(STALL_1_NAME))
        assert result["status"] == "success"
        assert result["stall_name"] == STALL_1_NAME


def test_publish_products_by_stall_name(
    merchant: Merchant, product_event_ids: List[EventId]
) -> None:
    """Test publishing all products in a stall"""
    with patch.object(merchant._nostr_client, "publish_product") as mock_publish:
        mock_publish.side_effect = itertools.cycle(product_event_ids)

        results = json.loads(merchant.publish_products_by_stall_name(STALL_1_NAME))
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


def test_profile_operations(merchant: Merchant, profile_event_id: EventId) -> None:
    """Test profile-related operations"""
    profile_data = json.loads(merchant.get_profile())
    assert profile_data["name"] == MERCHANT_NAME
    assert profile_data["description"] == MERCHANT_DESCRIPTION

    with patch.object(merchant._nostr_client, "publish_profile") as mock_publish:
        mock_publish.return_value = profile_event_id
        result = json.loads(merchant.publish_profile())
        assert isinstance(result, dict)
