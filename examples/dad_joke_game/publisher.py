"""
Publisher agent for the Dad Joke Game.
"""

from os import getenv
from pathlib import Path

from dotenv import load_dotenv

# --***---
from agno.agent import Agent  # type: ignore
from agno.models.openai import OpenAIChat  # type: ignore
from synvya_sdk import Namespace, NostrKeys, Profile, ProfileType, generate_keys
from synvya_sdk.agno import DadJokeGamerTools

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
    keys = NostrKeys.from_private_key(NSEC)

print(f"Public key: {keys.get_public_key('hex')}")

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
PROFILE_TYPE = ProfileType.GAMER_DADJOKE
HASHTAG = "publisher"

publisher_profile = Profile(keys.get_public_key())
publisher_profile.set_name(NAME)
publisher_profile.set_about(ABOUT)
publisher_profile.set_banner(BANNER)
publisher_profile.set_bot(True)
publisher_profile.set_display_name(DISPLAY_NAME)
publisher_profile.set_nip05(NIP05)
publisher_profile.set_picture(PICTURE)
publisher_profile.set_website(WEBSITE)
publisher_profile.set_namespace(NAMESPACE)
publisher_profile.set_profile_type(PROFILE_TYPE)
publisher_profile.add_hashtag(HASHTAG)


publisher_tools = DadJokeGamerTools(
    name=DISPLAY_NAME,
    relay=RELAY,
    private_key=keys.get_private_key(),
)

publisher_tools.set_profile(publisher_profile)


publisher = Agent(  # type: ignore[call-arg]
    name=DISPLAY_NAME,
    model=OpenAIChat(id="gpt-3.5-turbo", api_key=OPENAI_API_KEY),
    tools=[publisher_tools],
    show_tool_calls=True,
    debug_mode=False,
    add_history_to_messages=True,
    num_history_responses=5,
    read_chat_history=False,
    read_tool_call_history=False,
    # async_mode=True,
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
def publisher_cli() -> None:
    """
    Command-line interface for dad joke publisher agent.
    """
    print("\n🔹 Dad Joke Publisher Agent CLI (Press Ctrl+C to quit)\n")
    try:
        while True:
            response = publisher.run("""do your job""")
            print(
                f"\n🤖 Dad Joke Publisher Agent: {response.get_content_as_string()}\n"
            )
    except KeyboardInterrupt:
        print("\n👋 Goodbye!\n")


# Run the CLI
publisher_cli()
