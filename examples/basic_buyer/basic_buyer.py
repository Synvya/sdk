from os import getenv
from pathlib import Path
from typing import List, Tuple

import httpx
from dotenv import load_dotenv
from phi.agent import Agent  # type: ignore
from phi.model.openai import OpenAIChat  # type: ignore

from agentstr.buyer import Buyer
from agentstr.models import AgentProfile
from agentstr.nostr import Keys, generate_and_save_keys

# Environment variables
ENV_RELAY = "RELAY"
DEFAULT_RELAY = "wss://relay.damus.io"
ENV_KEY = "BUYER_AGENT_KEY"

# Buyer profile constants
NAME = "BusinessName"
DESCRIPTION = "I'm in the business of doing business."
PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"
DISPLAY_NAME = "Buyer Agent for Business Name Inc."

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

print(f"Private key: {keys.secret_key().to_bech32()}")
print(f"Public key: {keys.public_key().to_bech32()}")

# Load or use default relay
relay = getenv(ENV_RELAY)
if relay is None:
    relay = DEFAULT_RELAY

# Initialize a buyer profile
buyer_profile = AgentProfile(keys=keys)
buyer_profile.set_name(NAME)
buyer_profile.set_about(DESCRIPTION)
buyer_profile.set_display_name(DISPLAY_NAME)
buyer_profile.set_picture(PICTURE)

buyer_agent = Agent(  # type: ignore[call-arg]
    name="Buyer Assistant",
    model=OpenAIChat(id="gpt-4o"),
    tools=[Buyer(buyer_profile=buyer_profile, relay=relay)],
    show_tool_calls=False,
    debug_mode=False,
    async_mode=True,
    instructions=[
        """The Buyer Toolkit functions return JSON arrays.
        Answer me in a friendly and engaging manner. When I ask you what can I do in a certain location, 
        you should first look for sellers in that location, then retrieve their products, 
        and then suggest that I purchase some of their products. Share all the information you have 
        about the stalls, products and the sellers. Ignore sellers with the word "test" in their name.
        When I tell you that I want to buy something, use the purchase_product function
        to purchase the product. Just put together a string with what I'm asking to 
        purchase and pass it to the purchase_product function.
        """.strip(),
    ],
)

# agent.print_response("List the products of the merchant")
buyer_agent.cli_app(stream=False)
