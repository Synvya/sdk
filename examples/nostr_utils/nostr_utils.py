"""
Nostr utility functions.
"""

from os import getenv
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from agentstr import EventId, Keys, NostrClient, generate_and_save_keys

ENV_KEY = "NOSTR_UTILS_KEY"

# Get directory where the script is located
script_dir = Path(__file__).parent
# Load .env from the script's directory
load_dotenv(script_dir / ".env")

ENV_RELAY = "RELAY"
DEFAULT_RELAY = "wss://relay.damus.io"

# Load or use default relay
RELAY = getenv(ENV_RELAY)
if RELAY is None:
    RELAY = DEFAULT_RELAY
# Load or generate keys
NSEC = getenv(ENV_KEY)
if NSEC is None:
    keys = generate_and_save_keys(env_var=ENV_KEY, env_path=script_dir / ".env")
else:
    keys = Keys.parse(NSEC)

print(f"Private Key: {keys.secret_key().to_bech32()}")
print(f"Public Key: {keys.public_key().to_bech32()}")

event_list: List[str] = [
    "9c5a83bf63f8ac82e750fdd92fdc9cc07c4358895ee362beada600f048395e73",
    "e6f10dddb85645067d06944c4d4721c18b7834ff61c1b3c50abad868e5dd9030",
    "da53f3e7490da3cee24831bc01ac31912e47ca09bf7b523b7a86f00746bee7f8",
    "d0d27c891d9d93389562bee801606c9e1d26f69f773881c7e5a8a866df1af0b9",
    "5f787ee08638e5d40ddb3513c08c7c4765cb76cd0858823a1dff8c2d8a6463fa",
]

nostr_client = NostrClient(relay=RELAY, nsec=keys.secret_key().to_bech32())

for event in event_list:
    event_id = EventId.parse(event)
    event = nostr_client.delete_event(event_id)
    print(event)
