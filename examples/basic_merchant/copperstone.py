"""
Sample data for the Copperstone merchant.
"""

from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from agentstr import (
    AgentProfile,
    Keys,
    MerchantProduct,
    MerchantStall,
    ShippingCost,
    ShippingMethod,
    generate_and_save_keys,
)

ENV_KEY = "COPPERSTONE_AGENT_KEY"

# Get directory where the script is located
script_dir = Path(__file__).parent
# Load .env from the script's directory
load_dotenv(script_dir / ".env")

# Load or generate keys
nsec = getenv(ENV_KEY)
if nsec is None:
    keys = generate_and_save_keys(env_var=ENV_KEY, env_path=script_dir / ".env")
else:
    keys = Keys.parse(nsec)

# --*-- Merchant info
COPPERSTONE_NAME = "Copperstone"
COPPERSTONE_DESCRIPTION = "Copperstone Family Spaguetti Restaurant"
COPPERSTONE_PICTURE = "https://i.nostr.build/TL0QeUTb2TItb03y.png"
COPPERSTONE_CURRENCY = "USD"
COPPERSTONE_GEOHASH = "C23Q7U36W"


# --*-- Stall for ride at 11am
COPPERSTONE_STALL_NAME = "Copperstone"
COPPERSTONE_STALL_ID = "copperstone-stall-snoqualmie"
COPPERSTONE_STALL_DESCRIPTION = """
Italian dining with a warm environment, impeccable service & friendly staff. Serving
large, family-style portions that accommodate a wide variety of tastes. No Dish is
pre-cooked.... we take pride in serving you fresh, simply delicious cuisine!
Opening Hours:
 - Monday Closed 
 - Tuesday-Thursday 11:30AM – 8:30PM
 - Friday & Saturday 11:30AM – 9:30PM
 - Sunday 11:30AM – 8:30PM
Address: 8072 Railroad Ave, Snoqualmie, WA 98065
""".strip()

# --*-- Shipping info
COPPERSTONE_SHIPPING_ZONE_NAME = "Worldwide"
COPPERSTONE_SHIPPING_ZONE_ID = "copperstone-sz"
COPPERSTONE_SHIPPING_ZONE_REGIONS = ["Eat Here", "Take Out"]

# --*-- NRM Product info
COPPERSTONE_PRODUCT_ID = "copperstone-reservation"
COPPERSTONE_PRODUCT_IMAGE = "https://i.nostr.build/pqRHZy6dTFplHwkQ.png"
COPPERSTONE_QUANTITY = 90
COPPERSTONE_PRODUCT_NAME = "Dine in reservation"
COPPERSTONE_PRODUCT_DESCRIPTION = (
    "Dine in reservation for Copperstone Family Spaguetti Restaurant"
)
COPPERSTONE_PRODUCT_PRICE = 0


# --*-- Define Shipping methods for stalls (nostr SDK type)
shipping_method_copperstone = (
    ShippingMethod(id=COPPERSTONE_SHIPPING_ZONE_ID, cost=0)
    .name(COPPERSTONE_SHIPPING_ZONE_NAME)
    .regions(COPPERSTONE_SHIPPING_ZONE_REGIONS)
)

# --*-- Define Shipping costs for products (nostr SDK type)
shipping_cost_copperstone = ShippingCost(id=COPPERSTONE_SHIPPING_ZONE_ID, cost=0)

# --*-- define stalls (using ShippingMethod)
copperstone_stall = MerchantStall(
    id=COPPERSTONE_STALL_ID,
    name=COPPERSTONE_STALL_NAME,
    description=COPPERSTONE_STALL_DESCRIPTION,
    currency=COPPERSTONE_CURRENCY,
    shipping=[shipping_method_copperstone],
    geohash=COPPERSTONE_GEOHASH,
)

# --*-- define products (using ShippingZone)
copperstone_reservation = MerchantProduct(
    id=COPPERSTONE_PRODUCT_ID,
    stall_id=COPPERSTONE_STALL_ID,
    name=COPPERSTONE_PRODUCT_NAME,
    description=COPPERSTONE_PRODUCT_DESCRIPTION,
    images=[COPPERSTONE_PRODUCT_IMAGE],
    currency=COPPERSTONE_CURRENCY,
    price=COPPERSTONE_PRODUCT_PRICE,
    quantity=COPPERSTONE_QUANTITY,
    shipping=[shipping_cost_copperstone],
    categories=["reservation", "italian", "family", "lunch", "dinner"],
    specs=[
        ["menu", "starters"],
        ["menu", "pasta"],
        ["menu", "salads"],
        ["menu", "desserts"],
        ["menu", "drinks"],
    ],
)

profile = AgentProfile(keys=keys)
profile.set_name(COPPERSTONE_NAME)
profile.set_about(COPPERSTONE_DESCRIPTION)
profile.set_picture(COPPERSTONE_PICTURE)

stalls = [copperstone_stall]
products = [copperstone_reservation]
