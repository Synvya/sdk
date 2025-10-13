"""
This example shows how to create a basic merchant agent.
"""

import asyncio
from os import getenv

from mtp import keys, products, profile, stalls

# --***---
from agno.agent import Agent  # type: ignore
from agno.models.openai import OpenAIChat  # type: ignore
from synvya_sdk import KeyEncoding
from synvya_sdk.agno import MerchantTools

# --***---
# Collect sample data from the merchant examples
# Remove comment from the one you want to use


# from mtp import products, profile, stalls


# Environment variables
ENV_RELAY = "RELAY"
DEFAULT_RELAY = "wss://nos.lol"


# Load or use default relay
RELAY = getenv(ENV_RELAY)
if RELAY is None:
    RELAY = DEFAULT_RELAY

OPENAI_API_KEY = getenv("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not set")
# print(f"OpenAI API key: {openai_api_key}")

print(f"Private Key: {keys.get_private_key(KeyEncoding.BECH32)}")
print(f"Public Key (bech32): {keys.get_public_key(KeyEncoding.BECH32)}")
print(f"Public Key (hex): {keys.get_public_key(KeyEncoding.HEX)}")

merchant_tools = asyncio.run(
    MerchantTools.create(
        relays=RELAY,
        private_key=keys.get_private_key(KeyEncoding.BECH32),
        stalls=stalls,
        products=products,
    )
)

asyncio.run(merchant_tools.async_set_profile(profile))

merchant = Agent(  # type: ignore[call-arg]
    name=f"AI Agent for {profile.get_name()}",
    model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
    tools=[merchant_tools],
    debug_mode=False,
    num_history_runs=10,
    read_chat_history=False,
    read_tool_call_history=False,
    instructions=[
        """
        The Merchant Toolkit functions return JSON arrays. Provide output
        as conversational text and not JSON or markup language. You are
        publishing a merchant profile and products to the Nostr network.
        If you encounter any errors, first try again, then, let me know
        with specific details for each error message.

        To publish a single product or a single stall, use the tools
        `async_publish_product` and `async_publish_stall` with the exact name
        of the product or stall. To find the exact name of the product or stall,
        use the tool `get_products` or `get_stalls` and match the name property
        to the input provided by the user.

        When you receive an order, you must take one of the following actions:
        - Process the order if the order value (price x quantity) is less than
        1,000,000 sats.
        - Trigger a manual workflow for the order if the order value (price x quantity)
        is greater than 1,000,000 sats.

	    To determine the price, use the tool get_products to find the product ordered
	    in your database and its price.

	    To process an order follow these steps:
        1. Use the tool `async_send_payment_request` with the following arguments:
        - buyer
	    - order
        - The same kind that was used in the order received ("kind:4" or "kind:14")
	    - "BTC" as payment type
	    - "bc123456" as payment url

        2. Wait a few seconds and then use the tool `verify_payment` with
        the same arguments as `async_send_payment_request`
        3. If the payment is verified, use the tool `async_send_payment_verification`
        with the arguments:
        - buyer
        - order
        - The same kind that was used in the order received ("kind:4" or "kind:14")
        """.strip(),
    ],
)


# Command-line interface with response storage
async def merchant_cli() -> None:
    """
    Command-line interface for example merchant agent.
    """
    # publishing stalls
    print("Publishing all stalls")
    response = await merchant.arun("publish all stalls")
    print(f"\n🤖 Merchant Agent: {response.get_content_as_string()}\n")

    print("Publishing all products")
    response = await merchant.arun(
        "publish all products, one at a time, wait 2 seconds in between each product"
    )
    print(f"\n🤖 Merchant Agent: {response.get_content_as_string()}\n")

    print("\n🔹 Merchant Agent CLI (Press Ctrl+C to quit)\n")
    while True:
        response = await merchant.arun(
            """listen for orders with a timeout of 10 seconds.
            if no orders are received, respond with '...waiting for orders...
            press ctrl+c to quit'
            """
        )
        print(f"\n🤖 Merchant Agent: {response.get_content_as_string()}\n")


# Run the CLI
if __name__ == "__main__":
    asyncio.run(merchant_cli())
