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
