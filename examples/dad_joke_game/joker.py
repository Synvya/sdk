"""
Joker agent for the Dad Joke Game.
"""

from os import getenv
from pathlib import Path

from dotenv import load_dotenv

# --***---
from agno.agent import Agent  # type: ignore
from agno.models.openai import OpenAIChat  # type: ignore
from synvya_sdk import Namespace, NostrKeys, Profile, ProfileType, generate_keys
from synvya_sdk.agno import DadJokeGamerTools

ENV_KEY = "JOKER_AGENT_KEY"
ENV_RELAY = "RELAY"
DEFAULT_RELAY = "wss://relay.damus.io"

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

print(f"Public key: {keys.get_public_key("hex")}")

# Load or use default relay
RELAY = getenv(ENV_RELAY)
if RELAY is None:
    RELAY = DEFAULT_RELAY

OPENAI_API_KEY = getenv("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not set")

# --*-- Merchant info
ABOUT = "The master of dad jokes"
BANNER = "https://i.nostr.build/OfJaUsM6hsomPb5h.webp"
DISPLAY_NAME = "Playing the Dad Joke game for a living"
NAME = "joker"
NIP05 = "joker@synvya.com"
PICTURE = "https://i.nostr.build/TRzCCrLTjrbSvhtP.png"
WEBSITE = "https://synvya.com"
NAMESPACE = Namespace.GAMER
PROFILE_TYPE = ProfileType.GAMER_DADJOKE
HASHTAG = "joker"

joker_profile = Profile(keys.get_public_key())
joker_profile.set_name(NAME)
joker_profile.set_about(ABOUT)
joker_profile.set_banner(BANNER)
joker_profile.set_bot(True)
joker_profile.set_display_name(DISPLAY_NAME)
joker_profile.set_nip05(NIP05)
joker_profile.set_picture(PICTURE)
joker_profile.set_website(WEBSITE)
joker_profile.set_namespace(NAMESPACE)
joker_profile.set_profile_type(PROFILE_TYPE)
joker_profile.add_hashtag(HASHTAG)


joker_tools = DadJokeGamerTools(
    name=DISPLAY_NAME,
    relay=RELAY,
    private_key=keys.get_private_key(),
)

joker_tools.set_profile(joker_profile)


joker = Agent(  # type: ignore[call-arg]
    name=DISPLAY_NAME,
    model=OpenAIChat(id="gpt-3.5-turbo", api_key=OPENAI_API_KEY),
    tools=[joker_tools],
    show_tool_calls=True,
    debug_mode=False,
    add_history_to_messages=True,
    num_history_responses=5,
    read_chat_history=False,
    read_tool_call_history=False,
    # async_mode=True,
    instructions=[
        """
        You are a gamer agent playing the Dad Joke Game with the role of a joker.

        Your job is to take the following steps in order:
        1. Listen for a joke request from the publisher with the tool
        `listen_for_joke_request`.
        2. If and when you receive a joke request, you must respond with a dad joke
        using the tool `submit_joke`.
        

        You will not use any other tools.

        You will repeat the steps above for every job iteration for as long as you are running.
        """.strip(),
    ],
)


# Command-line interface with response storage
def joker_cli() -> None:
    """
    Command-line interface for dad joke joker agent.
    """
    print("\n🔹 Dad Joke Joker Agent CLI (Press Ctrl+C to quit)\n")
    while True:
        response = joker.run("""do your job""")
        print(f"\n🤖 Dad Joke Joker Agent: {response.get_content_as_string()}\n")


# Run the CLI
joker_cli()
