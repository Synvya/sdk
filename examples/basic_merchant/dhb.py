"""
Sample data for the Dark Horse Brew Coffee merchant.
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

ENV_KEY = "DHB_AGENT_KEY"

# Get directory where the script is located
script_dir = Path(__file__).parent
# Load .env from the script's directory
load_dotenv(script_dir / ".env")

# Load or generate keys
NSEC = getenv(ENV_KEY)
if NSEC is None:
    keys = generate_and_save_keys(env_var=ENV_KEY, env_path=script_dir / ".env")
else:
    keys = Keys.parse(NSEC)

# --*-- Merchant info
DHB_NAME = "Dark Horse Brew Coffee"
DHB_DESCRIPTION = (
    "Great tasting coffee should be accessible to our locals all year round"
)
DHB_PICTURE = "https://i.nostr.build/XbsM7zc1hBHSZKhn.png"
DHB_CURRENCY = "USD"
DHB_GEOHASH = "C23Q7U36W"


# --*-- Stall for ride at 11am
DHB_STALL_NAME = "Dark Horse Brew Coffee"
DHB_STALL_ID = "dhb-stall-snoqualmie"  # "212a26qV"
DHB_STALL_DESCRIPTION = """
Dark Horse Brew is made up of a passionate team of coffee lovers who believe that great 
tasting coffee should be accessible to our locals all year round. With drive-thru and
walk-up coffee stands in both downtown Snoqualmie WA and downtown Redmond WA so you can
always grab a quality drink or snack for your morning commute, on your lunch break, or
even on your way home. Whatever the occasion, we’re here to offer best-in-service coffee
products for you whenever you need it.

Address: 7936 Railroad Ave, Snoqualmie, WA 98065
""".strip()

# --*-- Shipping info
DHB_SHIPPING_ZONE_NAME = "Drive Thru"
DHB_SHIPPING_ZONE_ID = "dhb-sz"
DHB_SHIPPING_ZONE_REGIONS = ["Drive Thru"]

# --*-- NRM Product info
DHB_PRODUCT_ID = "dhb-latte"
DHB_PRODUCT_IMAGE = "https://i.nostr.build/53rGnQg7R9HcvjWY.png"
DHB_QUANTITY = 90
DHB_PRODUCT_NAME = "Dark Horse Brew Latte"
DHB_PRODUCT_DESCRIPTION = "A latte with a shot of espresso and a layer of foam."
DHB_PRODUCT_PRICE = 5


# --*-- Define Shipping methods for stalls (nostr SDK type)
shipping_method_dhb = (
    ShippingMethod(id=DHB_SHIPPING_ZONE_ID, cost=0)
    .name(DHB_SHIPPING_ZONE_NAME)
    .regions(DHB_SHIPPING_ZONE_REGIONS)
)

# --*-- Define Shipping costs for products (nostr SDK type)
shipping_cost_dhb = ShippingCost(id=DHB_SHIPPING_ZONE_ID, cost=0)

# --*-- define stalls (using ShippingMethod)
dhb_stall = MerchantStall(
    id=DHB_STALL_ID,
    name=DHB_STALL_NAME,
    description=DHB_STALL_DESCRIPTION,
    currency=DHB_CURRENCY,
    shipping=[shipping_method_dhb],
    geohash=DHB_GEOHASH,
)

# --*-- define products (using ShippingZone)
dhb_latte = MerchantProduct(
    id=DHB_PRODUCT_ID,
    stall_id=DHB_STALL_ID,
    name=DHB_PRODUCT_NAME,
    description=DHB_PRODUCT_DESCRIPTION,
    images=[DHB_PRODUCT_IMAGE],
    currency=DHB_CURRENCY,
    price=DHB_PRODUCT_PRICE,
    quantity=DHB_QUANTITY,
    shipping=[shipping_cost_dhb],
    categories=["coffee", "latte"],
    specs=[
        ["temperature", "hot"],
        ["temperature", "cold"],
        ["size", "small"],
        ["size", "medium"],
        ["size", "large"],
    ],
)

profile = AgentProfile(keys=keys)
profile.set_name(DHB_NAME)
profile.set_about(DHB_DESCRIPTION)
profile.set_picture(DHB_PICTURE)

stalls = [dhb_stall]
products = [dhb_latte]
