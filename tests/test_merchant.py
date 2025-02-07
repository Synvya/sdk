from typing import Literal, List
import json
import pytest
import itertools
from dotenv import load_dotenv
from os import getenv
from unittest.mock import Mock, patch
from agentstr.marketplace import Merchant, Profile, NostrClient, ProductData, StallData, ShippingMethod, ShippingCost, EventId
from agentstr.nostr import PublicKey, Timestamp, Kind, Event, Keys, EventBuilder, Metadata

load_dotenv()

RELAY = "wss://relay.damus.io"

# --*-- Merchant info
MERCHANT_NAME = "Merchant 1"
MERCHANT_DESCRIPTION = "Selling products peer to peer"
MERCHANT_PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"

# --*-- Stall info
STALL_1_NAME = "The Hardware Store"
STALL_1_ID = "212au4Pi" #"212a26qV"
STALL_1_DESCRIPTION = "Your neighborhood hardware store, now available online."
STALL_1_CURRENCY = "Sats"

STALL_2_NAME = "The Trade School"
STALL_2_ID = "c8762EFD"
STALL_2_DESCRIPTION = "Educational videos to put all your hardware supplies to good use."
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
def relay():
    return RELAY

@pytest.fixture
def profile_event_id():
    event_id = EventId(
        public_key=PublicKey.parse("bbd4a62e5612c5430f745bd116bac79fd186d14c1b859a02d5920f749c8a453b"),
        created_at=Timestamp.from_secs(1737436574),
        kind=Kind(0),
        tags=[],
        content="{\"name\":\"Synvya Inc\",\"about\":\"Agentic communications\",\"picture\":\"https://i.nostr.build/ocjZ5GlAKwrvgRhx.png\"}"
    )
    return event_id

@pytest.fixture
def merchant_profile():
    nsec = getenv("NSEC_KEY")
    profile = Profile(
        MERCHANT_NAME,
        MERCHANT_DESCRIPTION,
        MERCHANT_PICTURE,
        nsec
    )
    return profile

@pytest.fixture
def nostr_client():
    nsec = getenv("NSEC_KEY")
    return NostrClient(RELAY, nsec)

@pytest.fixture
def shipping_methods():
    return [
        ShippingMethod(
            id= SHIPPING_ZONE_1_ID,
            cost=10000
        ).name(SHIPPING_ZONE_1_NAME).regions(SHIPPING_ZONE_1_REGIONS),
        ShippingMethod(
            id= SHIPPING_ZONE_2_ID,
            cost=10000
        ).name(SHIPPING_ZONE_2_NAME).regions(SHIPPING_ZONE_2_REGIONS),
        ShippingMethod(
            id= SHIPPING_ZONE_3_ID,
            cost=10000
        ).name(SHIPPING_ZONE_3_NAME).regions(SHIPPING_ZONE_3_REGIONS)
    ]

@pytest.fixture
def shipping_costs():
    return [
        ShippingCost(id = SHIPPING_ZONE_1_ID, cost=5000),
        ShippingCost(id = SHIPPING_ZONE_2_ID, cost=5000),
        ShippingCost(id = SHIPPING_ZONE_3_ID, cost=0)
    ]

@pytest.fixture
def stalls(shipping_methods):
    return [
        StallData(id = STALL_1_ID,
                  name = STALL_1_NAME,
                  description = STALL_1_DESCRIPTION,
                  currency = STALL_1_CURRENCY,
                  shipping = [
                      shipping_methods[0],
                      shipping_methods[1]
                    ]
                ),
        StallData(id = STALL_2_ID,
                  name = STALL_2_NAME,
                  description = STALL_2_DESCRIPTION,
                  currency = STALL_2_CURRENCY,
                  shipping = [ 
                      shipping_methods[2]
                    ]
                )
    ]

@pytest.fixture
def products(shipping_costs):
    return [
        ProductData(
            id = PRODUCT_1_ID,
            stall_id = STALL_1_ID,
            name = PRODUCT_1_NAME,
            description = PRODUCT_1_DESCRIPTION,
            images = PRODUCT_1_IMAGES,
            currency = PRODUCT_1_CURRENCY,
            price = PRODUCT_1_PRICE,
            quantity = PRODUCT_1_QUANTITY,
            shipping = [shipping_costs[0], shipping_costs[1]],
            specs= None,
            categories=None
        ),
        ProductData(
            id = PRODUCT_2_ID,
            stall_id = STALL_1_ID,
            name = PRODUCT_2_NAME,
            description = PRODUCT_2_DESCRIPTION,
            images = PRODUCT_2_IMAGES,
            currency = PRODUCT_2_CURRENCY,
            price = PRODUCT_2_PRICE,
            quantity = PRODUCT_2_QUANTITY,
            shipping = [shipping_costs[0], shipping_costs[1]],
            specs= None,
            categories=None
        ),
        ProductData(
            id = PRODUCT_3_ID,
            stall_id = STALL_2_ID,
            name = PRODUCT_3_NAME,
            description = PRODUCT_3_DESCRIPTION,
            images = PRODUCT_3_IMAGES,
            currency = PRODUCT_3_CURRENCY,
            price = PRODUCT_3_PRICE,
            quantity = PRODUCT_3_QUANTITY,
            shipping = [shipping_costs[2]],
            specs= None,
            categories=None
        )
    ]

@pytest.fixture
def product_event_ids():
    #provide valid but dummy hex event id strings
    return [
        EventId.parse("d1441f3532a44772fba7c57eb7c71c94c3971246722ae6e372cf50c198af784a"),
        EventId.parse("b6a81ca6cbd5fa59e564208796a76af670a7a402ec0bb4621c999688ed10e43e"),
        EventId.parse("dc25ae17347de75763c7462d7b7e26011167b05a60c425e3cf9aecea753930e6")
    ]

@pytest.fixture
def stall_event_ids():
    #provide valid but dummy hex event id strings
    return [
        EventId.parse("c12fed92c3dd928fcce4a5d0a5ec608aa52687f4ac45fad6ef1b4895c19fec75"),
        EventId.parse("ecc04d51f124598abb7bd6830e169dbd4d97aef3bfc19a20ba07b99db709b893"),
    ]

def test_init(merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    assert isinstance(merchant.get_merchant_profile(), str)
    assert merchant.get_merchant_relay() == RELAY

def test_get_products(merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    products_result = merchant.get_products()
    assert len(products_result) == len(products)

def test_get_stalls(merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    output = merchant.get_stalls()
    json_output = json.loads(output)
    assert len(json_output) == len(stalls)

def test_publish_all_products(product_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_product') as mock_publish_product:
        mock_publish_product.side_effect = itertools.cycle(product_event_ids)
        output = merchant.publish_all_products()
        json_output = json.loads(output)
    assert len(json_output) == 0

def test_publish_all_products_error(merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_product') as mock_publish_product:
        mock_publish_product.side_effect = Exception("Error publishing product")
        output = merchant.publish_all_products()
        json_output = json.loads(output)
    assert len(json_output) == len(products)


def test_publish_all_stalls(stall_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_stall') as mock_publish_stall:
        mock_publish_stall.side_effect = itertools.cycle(stall_event_ids)
        output = merchant.publish_all_stalls()
        json_output = json.loads(output)
    assert len(json_output) == 0

def test_publish_all_stalls_error(merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_stall') as mock_publish_stall:
        mock_publish_stall.side_effect = Exception("Error publishing stall")
        output = merchant.publish_all_stalls()
        json_output = json.loads(output)
    assert len(json_output) == len(stalls)

def test_publish_product(product_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_product') as mock_publish_product:
        mock_publish_product.return_value = itertools.cycle(product_event_ids)
        product = products[0]
        output = merchant.publish_product(product)
        json_output = json.loads(output)
    assert len(json_output) == 1

def test_publish_product_error(product_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_product') as mock_publish_product:
        mock_publish_product.side_effect = Exception("Error publishing product")
        product = products[0]
        output = merchant.publish_product(product)
        json_output = json.loads(output)
    assert len(json_output) == 0



def test_publish_product_by_name(product_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_product') as mock_publish_product:
        mock_publish_product.return_value = itertools.cycle(product_event_ids)
        product = products[0]
        output = merchant.publish_product_by_name(product.name)
        json_output = json.loads(output)
    assert len(json_output) == 1

def test_publish_product_by_name_error(product_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_product') as mock_publish_product:
        mock_publish_product.side_effect = Exception("Error publishing product")
        product = products[0]
        output = merchant.publish_product_by_name(product.name)
        json_output = json.loads(output)
    assert len(json_output) == 0

def test_publish_products_by_stall(product_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_product') as mock_publish_product:
        mock_publish_product.return_value = itertools.cycle(product_event_ids)
        stall = stalls[0]
        output = merchant.publish_products_by_stall(stall.name())
        json_output = json.loads(output)
    assert len(json_output) == 0

def test_publish_product_by_stall_error(product_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_product') as mock_publish_product:
        mock_publish_product.side_effect = Exception("Error publishing product")
        stall = stalls[0]
        output = merchant.publish_products_by_stall(stall.name())
        json_output = json.loads(output)
    assert len(json_output) > 0

def test_publish_stall(stall_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_stall') as mock_publish_stall:
        mock_publish_stall.return_value = itertools.cycle(stall_event_ids)
        stall = stalls[0]
        output = merchant.publish_stall(stall)
        json_output = json.loads(output)
    assert len(json_output) == 1

def test_publish_stall_error(stall_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_stall') as mock_publish_stall:
        mock_publish_stall.side_effect = Exception("Error publishing stall")
        stall = stalls[0]
        output = merchant.publish_stall(stall)
        json_output = json.loads(output)
    assert len(json_output) == 0


def test_publish_stall_by_name(stall_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_stall') as mock_publish_stall:
        mock_publish_stall.return_value = itertools.cycle(stall_event_ids)
        stall = stalls[0]
        output = merchant.publish_stall_by_name(stall.name)
        json_output = json.loads(output)
    assert len(json_output) == 1

def test_publish_stall_by_name_error(stall_event_ids, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_stall') as mock_publish_stall:
        mock_publish_stall.side_effect = Exception("Error publishing stall")
        stall = stalls[0]
        output = merchant.publish_stall_by_name(stall.name)
        json_output = json.loads(output)
    assert len(json_output) == 0


def test_publish_profile(profile_event_id, merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_profile') as mock_publish_profile:
        mock_publish_profile.return_value = profile_event_id
        result = merchant.publish_profile()
    assert isinstance(result, str)
    # You could also check if the result is a valid JSON string
    try:
        json.loads(result)
    except json.JSONDecodeError:
        pytest.fail("Result is not a valid JSON string")

def test_publish_profile_failure(merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    with patch.object(merchant.nostr_client, 'publish_profile') as mock_publish_profile:
        mock_publish_profile.side_effect = Exception("Test exception")
        with pytest.raises(RuntimeError):
            merchant.publish_profile()

def test_get_products(merchant_profile: Profile, relay, stalls: list[StallData], products: list[ProductData]):
    merchant = Merchant(merchant_profile, relay, stalls, products)
    output = merchant.get_products()
    assert isinstance(output, str)
    try:
        json.loads(output)
    except json.JSONDecodeError:
        assert False, "Output is not a valid JSON string"

