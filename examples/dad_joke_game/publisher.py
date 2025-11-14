"""
Publisher agent for the Dad Joke Game.
"""

import asyncio
import signal
import sys
from os import getenv
from pathlib import Path
from time import sleep

from dotenv import load_dotenv

# --***---
from agno.agent import Agent  # type: ignore
from agno.models.openai import OpenAIChat  # type: ignore
from synvya_sdk import (
    KeyEncoding,
    Label,
    Namespace,
    NostrKeys,
    Profile,
    generate_keys,
)
from synvya_sdk.agno import DadJokeGamerTools


def handle_sigint(signum: int, frame: object) -> None:
    print("\n👋 Goodbye!\n")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_sigint)

ENV_KEY = "PUBLISHER_AGENT_KEY"
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
    keys = NostrKeys(private_key=NSEC)

print(f"Public key: {keys.get_public_key(KeyEncoding.BECH32)}")

# Load or use default relay
RELAY = getenv(ENV_RELAY)
if RELAY is None:
    RELAY = DEFAULT_RELAY

OPENAI_API_KEY = getenv("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not set")

# --*-- Merchant info
ABOUT = "The master of the Dad Joke Game"
BANNER = "https://i.nostr.build/M7uowolaczuAEbUH.png"
DISPLAY_NAME = "Dad Joke Publisher"
NAME = "dadjokepublisher"
NIP05 = "dadjokepublisher@synvya.com"
PICTURE = "https://i.nostr.build/0OAu51gpwNmqhfNd.png"
WEBSITE = "https://synvya.com"
NAMESPACE = Namespace.GAMER
PROFILE_LABEL = Label.GAMER_DADJOKE.value
PROFILE_NAMESPACE = Namespace.GAMER.value
HASHTAG = "publisher"

publisher_profile = Profile(keys.get_public_key(KeyEncoding.BECH32))
publisher_profile.set_name(NAME)
publisher_profile.set_about(ABOUT)
publisher_profile.set_banner(BANNER)
publisher_profile.set_bot(True)
publisher_profile.set_display_name(DISPLAY_NAME)
publisher_profile.set_nip05(NIP05)
publisher_profile.set_picture(PICTURE)
publisher_profile.set_website(WEBSITE)
publisher_profile.set_namespace(NAMESPACE)
publisher_profile.add_label(PROFILE_LABEL, PROFILE_NAMESPACE)
publisher_profile.add_hashtag(HASHTAG)


publisher_tools: DadJokeGamerTools = asyncio.run(
    DadJokeGamerTools.create(
        name=DISPLAY_NAME,
        relays=RELAY,
        private_key=keys.get_private_key(KeyEncoding.BECH32),
    )
)

asyncio.run(publisher_tools.async_set_profile(publisher_profile))


publisher = Agent(  # type: ignore[call-arg]
    name=DISPLAY_NAME,
    model=OpenAIChat(id="gpt-3.5-turbo", api_key=OPENAI_API_KEY),
    tools=[publisher_tools],
    debug_mode=False,
    num_history_runs=10,
    read_chat_history=False,
    read_tool_call_history=False,
    instructions=[
        """
        You are a gamer agent playing the Dad Joke Game with the role of a publisher.

        Your job is to contant other gamer agents with the role of a joker to get a joke
        from them and publish it to the Nostr network.

        Your job is to take the following steps in order:
        1. Use the tool `find_joker` to find a joker to whom you will send a joke
        request.
        2. Use the tool `request_joke` to request a joke from the joker you found.
        3. Use the tool `listen_for_joke` to listen for a joke from the joker you
        submitted your request to with a timeout of 60 seconds. If you don't receive
        anything after 60 seconds, start again from step 1.
        4. Analyze the received joke to determine if it's appropriate
        (as in not offensive and suitable for all ages).
        5. If it is appropriate, use the tool `publish_joke` to publish the received
        joke to the Nostr network. If it's not appropriate, do nothing.

        You will repeat the steps above for every job iteration for as long as you
        are running.
        """.strip(),
    ],
)


# Command-line interface with response storage
async def publisher_cli() -> None:
    """
    Command-line interface for dad joke publisher agent.
    """
    print("\n🔹 Dad Joke Publisher Agent CLI (Press Ctrl+C to quit)\n")
    try:
        while True:
            response = await publisher.arun("""do your job""")
            print(
                f"\n🤖 Dad Joke Publisher Agent: {response.get_content_as_string()}\n"
            )
            sleep(3600)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!\n")


# Run the CLI
if __name__ == "__main__":
    asyncio.run(publisher_cli())
