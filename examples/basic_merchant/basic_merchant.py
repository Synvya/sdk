"""
This example shows how to create a basic merchant agent.
"""

from os import getenv

from mtp import keys, products, profile, stalls

# --***---
from agno.agent import Agent  # type: ignore
from agno.models.openai import OpenAIChat  # type: ignore
from synvya_sdk.agno import SellerTools

# --***---
# Collect sample data from the merchant examples
# Remove comment from the one you want to use


# from mtp import products, profile, stalls


# Environment variables
ENV_RELAY = "RELAY"
DEFAULT_RELAY = "wss://relay.damus.io"


# Load or use default relay
RELAY = getenv(ENV_RELAY)
if RELAY is None:
    RELAY = DEFAULT_RELAY

OPENAI_API_KEY = getenv("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not set")
# print(f"OpenAI API key: {openai_api_key}")

merchant = Agent(  # type: ignore[call-arg]
    name=f"AI Agent for {profile.get_name()}",
    model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
    tools=[
        SellerTools(
            relay=RELAY,
            private_key=keys.get_private_key(),
            stalls=stalls,
            products=products,
        )
    ],
    show_tool_calls=True,
    debug_mode=False,
    add_history_to_messages=True,
    num_history_responses=10,
    read_chat_history=True,
    read_tool_call_history=True,
    # async_mode=True,
    instructions=[
        """
        The Merchant Toolkit functions return JSON arrays. Provide output
        as conversational text and not JSON or markup language. You are
        publishing a merchant profile and products to the Nostr network.
        If you encounter any errors, first try again, then, let me know
        with specific details for each error message.
        """.strip(),
    ],
)


# Command-line interface with response storage
def merchant_cli() -> None:
    """
    Command-line interface for example merchant agent.
    """
    print("\n🔹 Merchant Agent CLI (Type 'exit' to quit)\n")
    while True:
        user_query = input("💬 You: ")
        if user_query.lower() in ["exit", "quit"]:
            print("\n👋 Exiting Merchant Agent CLI. Goodbye!\n")
            break

        response = merchant.run(user_query)  # Get response from agent
        print(f"\n🤖 Merchant Agent: {response.get_content_as_string()}\n")


# Run the CLI
merchant_cli()
