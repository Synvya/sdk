from os import getenv
from pathlib import Path
from typing import List, Tuple

import httpx
from dotenv import load_dotenv
from phi.agent import Agent  # type: ignore
from phi.model.openai import OpenAIChat  # type: ignore

from agentstr.buyer import Buyer
from agentstr.nostr import AgentProfile, Keys, generate_and_save_keys

# Environment variables
ENV_RELAY = "RELAY"
DEFAULT_RELAY = "wss://relay.damus.io"
ENV_KEY = "NSEC_BASIC_BUYER_KEY"

# Buyer profile constants
NAME = "BusinessName"
DESCRIPTION = "I'm in the business of doing business."
PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"
DISPLAY_NAME = "Buyer Agent for Business Name Inc."

# Load environment variables
load_dotenv()

# Load or generate keys
nsec = getenv(ENV_KEY)
if nsec is None:
    keys = generate_and_save_keys(env_var=ENV_KEY)
else:
    keys = Keys.parse(nsec)

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
    show_tool_calls=True,
    debug_mode=True,
    async_mode=True,
    instructions=[
        "The Buyer Toolkit functions return JSON arrays. Provide these JSON arrays back to the console as output."
    ],
)

# agent.print_response("List the products of the merchant")
buyer_agent.cli_app(stream=False)
