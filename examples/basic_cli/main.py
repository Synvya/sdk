from os import getenv
from pathlib import Path
from typing import List, Tuple

import httpx
from dotenv import load_dotenv
from phi.agent import Agent  # type: ignore
from phi.model.openai import OpenAIChat  # type: ignore

from agentstr.merchant import (
    Merchant,
    MerchantProduct,
    MerchantStall,
    Profile,
    ShippingCost,
    ShippingMethod,
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

# --*-- Define Shipping methods for stalls (nostr SDK type)
shipping_method_1 = (
    ShippingMethod(id=SHIPPING_ZONE_1_ID, cost=5000)
    .name(SHIPPING_ZONE_1_NAME)
    .regions(SHIPPING_ZONE_1_REGIONS)
)

shipping_method_2 = (
    ShippingMethod(id=SHIPPING_ZONE_2_ID, cost=5000)
    .name(SHIPPING_ZONE_2_NAME)
    .regions(SHIPPING_ZONE_2_REGIONS)
)

shipping_method_3 = (
    ShippingMethod(id=SHIPPING_ZONE_3_ID, cost=0)
    .name(SHIPPING_ZONE_3_NAME)
    .regions(SHIPPING_ZONE_3_REGIONS)
)

# --*-- Define Shipping costs for products (nostr SDK type)
shipping_cost_1 = ShippingCost(id=SHIPPING_ZONE_1_ID, cost=1000)
shipping_cost_2 = ShippingCost(id=SHIPPING_ZONE_2_ID, cost=2000)
shipping_cost_3 = ShippingCost(id=SHIPPING_ZONE_3_ID, cost=3000)

# --*-- define stalls (using ShippingMethod)
test_stall_1 = MerchantStall(
    id=STALL_1_ID,
    name=STALL_1_NAME,
    description=STALL_1_DESCRIPTION,
    currency=STALL_1_CURRENCY,
    shipping=[shipping_method_1, shipping_method_2],
)

test_stall_2 = MerchantStall(
    id=STALL_2_ID,
    name=STALL_2_NAME,
    description=STALL_2_DESCRIPTION,
    currency=STALL_2_CURRENCY,
    shipping=[shipping_method_3],  # Uses ShippingMethod
)

# --*-- define products (using ShippingZone)
test_product_1 = MerchantProduct(
    id=PRODUCT_1_ID,
    stall_id=STALL_1_ID,
    name=PRODUCT_1_NAME,
    description=PRODUCT_1_DESCRIPTION,
    images=PRODUCT_1_IMAGES,
    currency=PRODUCT_1_CURRENCY,
    price=PRODUCT_1_PRICE,
    quantity=PRODUCT_1_QUANTITY,
    shipping=[shipping_cost_1, shipping_cost_2],
    categories=None,
    specs=[],  # List of lists of strings, e.g. [["Color", "Red"], ["Size", "Large"]]
)

test_product_2 = MerchantProduct(
    id=PRODUCT_2_ID,
    stall_id=STALL_1_ID,
    name=PRODUCT_2_NAME,
    description=PRODUCT_2_DESCRIPTION,
    images=PRODUCT_2_IMAGES,
    currency=PRODUCT_2_CURRENCY,
    price=PRODUCT_2_PRICE,
    quantity=PRODUCT_2_QUANTITY,
    shipping=[shipping_cost_1, shipping_cost_2],
    categories=None,
    specs=[],  # List of lists of strings
)

test_product_3 = MerchantProduct(
    id=PRODUCT_3_ID,
    stall_id=STALL_2_ID,
    name=PRODUCT_3_NAME,
    description=PRODUCT_3_DESCRIPTION,
    images=PRODUCT_3_IMAGES,
    currency=PRODUCT_3_CURRENCY,
    price=PRODUCT_3_PRICE,
    quantity=PRODUCT_3_QUANTITY,
    shipping=[shipping_cost_3],
    categories=None,
    specs=[],  # List of lists of strings
)

nsec = getenv("NSEC_BASIC_CLI_KEY")
if nsec:
    print(f"nsec: {nsec}")
else:
    print(f"No NSEC found")


test_merchant = Profile(MERCHANT_NAME, MERCHANT_DESCRIPTION, MERCHANT_PICTURE, nsec)


agent = Agent(  # type: ignore[call-arg]
    name="Merchant Assistant",
    model=OpenAIChat(id="gpt-4o"),
    tools=[
        Merchant(
            merchant_profile=test_merchant,
            relay=RELAY,
            stalls=[test_stall_1, test_stall_2],
            products=[test_product_1, test_product_2, test_product_3],
        )
    ],
    show_tool_calls=True,
    debug_mode=True,
    async_mode=True,
    instructions=[
        "The Merchant Toolkit functions return JSON arrays. Provide these JSON arrays back to the console as output."
    ],
)

# agent.print_response("List the products of the merchant")
agent.cli_app(stream=False)
