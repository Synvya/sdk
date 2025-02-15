## --*-- Merchant Test Profile Sample Data --*--
## Matches the Merchant Test Profile used in tests/*. See tests/conftest.py for details.
#####################################

from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from agentstr.models import AgentProfile, MerchantProduct, MerchantStall
from agentstr.nostr import Keys, ShippingCost, ShippingMethod, generate_and_save_keys

# Run this example to generate the data used by tests/*
# This example will create a nsec private key in .env under MTP_AGENT_KEY.
# Use this key in tests/conftest.py merchant_keys fixture to match the merchant profile.
ENV_KEY = "MTP_AGENT_KEY"

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
NAME = "Merchant Test Profile"
DESCRIPTION = "A merchant test profile"
PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"
CURRENCY = "Sats"
GEOHASH = "C23Q7U36W"

shipping_methods = [
    ShippingMethod(id="64be11rM", cost=10000)
    .name("North America")
    .regions(["Canada", "Mexico", "USA"]),
    ShippingMethod(id="d041HK7s", cost=20000)
    .name("Rest of the World")
    .regions(["All other countries"]),
    ShippingMethod(id="R8Gzz96K", cost=0).name("Worldwide").regions(["Worldwide"]),
]

shipping_costs = [
    ShippingCost(id="64be11rM", cost=5000),
    ShippingCost(id="d041HK7s", cost=5000),
    ShippingCost(id="R8Gzz96K", cost=0),
]

stalls = [
    MerchantStall(
        id="212au4Pi",
        name="The Hardware Store",
        description="Your neighborhood hardware store, now available online.",
        currency=CURRENCY,
        shipping=[shipping_methods[0], shipping_methods[1]],
        geohash=GEOHASH,
    ),
    MerchantStall(
        id="212au4Ph",
        name="The Trade School",
        description="Educational videos to put all your hardware supplies to good use.",
        currency=CURRENCY,
        shipping=[shipping_methods[2]],
        geohash=GEOHASH,
    ),
]

products = [
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

merchant = AgentProfile(keys=keys)
merchant.set_name(NAME)
merchant.set_about(DESCRIPTION)
merchant.set_picture(PICTURE)
