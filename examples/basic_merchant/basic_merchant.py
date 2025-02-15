from os import getenv

# --***---
# Collect sample data from the merchant examples
# Remove comment from the one you want to use
# from nrm import merchant, products, stalls
from mtp import merchant, products, stalls

# --***---
from phi.agent import Agent  # type: ignore
from phi.model.openai import OpenAIChat  # type: ignore

from agentstr.merchant import Merchant

# Environment variables
ENV_RELAY = "RELAY"
DEFAULT_RELAY = "wss://relay.damus.io"


# Load or use default relay
relay = getenv(ENV_RELAY)
if relay is None:
    relay = DEFAULT_RELAY


# STALL_2_NAME = "The Trade School"
# STALL_2_ID = "c8762EFD"
# STALL_2_DESCRIPTION = (
#     "Educational videos to put all your hardware supplies to good use."
# )
# STALL_2_CURRENCY = "Sats"
# STALL_2_GEOHASH = "C23Q7U36W"


# SHIPPING_ZONE_1_NAME = "North America"
# SHIPPING_ZONE_1_ID = "64be11rM"
# SHIPPING_ZONE_1_REGIONS = ["Canada", "Mexico", "USA"]

# SHIPPING_ZONE_2_NAME = "Rest of the World"
# SHIPPING_ZONE_2_ID = "d041HK7s"
# SHIPPING_ZONE_2_REGIONS = ["All other countries"]

# SHIPPING_ZONE_3_NAME = "Worldwide"
# SHIPPING_ZONE_3_ID = "R8Gzz96K"
# SHIPPING_ZONE_3_REGIONS = ["Worldwide"]


# PRODUCT_3_NAME = "Shovel 101"
# PRODUCT_3_ID = "ccf00Rx1"
# PRODUCT_3_DESCRIPTION = "How to dig your own grave"
# PRODUCT_3_IMAGES = ["https://i.nostr.build/psL0ZtN4FZcmeiIh.png"]
# PRODUCT_3_CURRENCY = STALL_2_CURRENCY
# PRODUCT_3_PRICE = 1000
# PRODUCT_3_QUANTITY = 1000


# shipping_method_1 = (
#     ShippingMethod(id=SHIPPING_ZONE_1_ID, cost=5000)
#     .name(SHIPPING_ZONE_1_NAME)
#     .regions(SHIPPING_ZONE_1_REGIONS)
# )

# shipping_method_2 = (
#     ShippingMethod(id=SHIPPING_ZONE_2_ID, cost=5000)
#     .name(SHIPPING_ZONE_2_NAME)
#     .regions(SHIPPING_ZONE_2_REGIONS)
# )

# shipping_method_3 = (
#     ShippingMethod(id=SHIPPING_ZONE_3_ID, cost=0)
#     .name(SHIPPING_ZONE_3_NAME)
#     .regions(SHIPPING_ZONE_3_REGIONS)
# )


# shipping_cost_1 = ShippingCost(id=SHIPPING_ZONE_1_ID, cost=1000)
# shipping_cost_2 = ShippingCost(id=SHIPPING_ZONE_2_ID, cost=2000)
# shipping_cost_3 = ShippingCost(id=SHIPPING_ZONE_3_ID, cost=3000)


# test_stall_1 = MerchantStall(
#     id=STALL_1_ID,
#     name=STALL_1_NAME,
#     description=STALL_1_DESCRIPTION,
#     currency=STALL_1_CURRENCY,
#     shipping=[shipping_method_1, shipping_method_2],
#     geohash=STALL_1_GEOHASH,
# )

# test_stall_2 = MerchantStall(
#     id=STALL_2_ID,
#     name=STALL_2_NAME,
#     description=STALL_2_DESCRIPTION,
#     currency=STALL_2_CURRENCY,
#     shipping=[shipping_method_3],  # Uses ShippingMethod
#     geohash=STALL_2_GEOHASH,
# )


# test_product_1 = MerchantProduct(
#     id=PRODUCT_1_ID,
#     stall_id=STALL_1_ID,
#     name=PRODUCT_1_NAME,
#     description=PRODUCT_1_DESCRIPTION,
#     images=PRODUCT_1_IMAGES,
#     currency=PRODUCT_1_CURRENCY,
#     price=PRODUCT_1_PRICE,
#     quantity=PRODUCT_1_QUANTITY,
#     shipping=[shipping_cost_1, shipping_cost_2],
#     categories=None,
#     specs=[],  # List of lists of strings, e.g. [["Color", "Red"], ["Size", "Large"]]
# )

# test_product_2 = MerchantProduct(
#     id=PRODUCT_2_ID,
#     stall_id=STALL_1_ID,
#     name=PRODUCT_2_NAME,
#     description=PRODUCT_2_DESCRIPTION,
#     images=PRODUCT_2_IMAGES,
#     currency=PRODUCT_2_CURRENCY,
#     price=PRODUCT_2_PRICE,
#     quantity=PRODUCT_2_QUANTITY,
#     shipping=[shipping_cost_1, shipping_cost_2],
#     categories=None,
#     specs=[],  # List of lists of strings
# )

# test_product_3 = MerchantProduct(
#     id=PRODUCT_3_ID,
#     stall_id=STALL_2_ID,
#     name=PRODUCT_3_NAME,
#     description=PRODUCT_3_DESCRIPTION,
#     images=PRODUCT_3_IMAGES,
#     currency=PRODUCT_3_CURRENCY,
#     price=PRODUCT_3_PRICE,
#     quantity=PRODUCT_3_QUANTITY,
#     shipping=[shipping_cost_3],
#     categories=None,
#     specs=[],  # List of lists of strings
# )


# test_merchant = AgentProfile(keys=keys)
# test_merchant.set_name(MERCHANT_NAME)
# test_merchant.set_about(MERCHANT_DESCRIPTION)
# test_merchant.set_picture(MERCHANT_PICTURE)

# Assign sample data to variables


agent = Agent(  # type: ignore[call-arg]
    name=f"AI Agent for {merchant.get_name()}",
    model=OpenAIChat(id="gpt-4o"),
    tools=[
        Merchant(
            merchant_profile=merchant,
            relay=relay,
            stalls=stalls,
            products=products,
        )
    ],
    show_tool_calls=False,
    debug_mode=False,
    async_mode=True,
    instructions=[
        """
        The Merchant Toolkit functions return JSON arrays. Provide output as conversational
        text and not JSON or markup language. You are publishing a merchant profile and
        products to the Nostr network. If you encounter any errors, first try again,
        then, let me know with specific details for each error message.
        """.strip(),
    ],
)

# agent.print_response("List the products of the merchant")
agent.cli_app(stream=False)
