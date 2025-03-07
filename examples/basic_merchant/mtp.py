"""
Sample data for the Merchant Test Profile merchant.
"""

from os import getenv
from pathlib import Path

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

ENV_KEY = "MTP_AGENT_KEY"

# Get directory where the script is located
script_dir = Path(__file__).parent
# Load .env from the script's directory
load_dotenv(script_dir / ".env")

# Load or generate keys
NSEC = getenv(ENV_KEY)
if NSEC is None:
    keys = generate_keys(env_var=ENV_KEY, env_path=script_dir / ".env")
else:
    keys = NostrKeys.from_private_key(NSEC)

# --*-- Merchant info
NAME = "Merchant Test Profile"
DESCRIPTION = "A merchant test profile"
PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"
CURRENCY = "Sats"
GEOHASH = "000000000"
WEBSITE = "https://merchant.test"

stall_shipping_methods = [
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

product_shipping_costs = [
    ProductShippingCost(psc_id="64be11rM", psc_cost=5000),
    ProductShippingCost(psc_id="d041HK7s", psc_cost=5000),
    ProductShippingCost(psc_id="R8Gzz96K", psc_cost=0),
]

stalls = [
    Stall(
        id="212au4Pi",
        name="The Hardware Store",
        description="Your neighborhood hardware store, now available online.",
        currency=CURRENCY,
        shipping=[stall_shipping_methods[0], stall_shipping_methods[1]],
        geohash=GEOHASH,
    ),
    Stall(
        id="212au4Ph",
        name="The Trade School",
        description="Educational videos to put all your hardware supplies to good use.",
        currency=CURRENCY,
        shipping=[stall_shipping_methods[2]],
        geohash=GEOHASH,
    ),
]

products = [
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

profile = Profile(keys.get_public_key())
profile.set_name(NAME)
profile.set_about(DESCRIPTION)
profile.set_picture(PICTURE)
profile.set_website(WEBSITE)
