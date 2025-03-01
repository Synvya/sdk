"""
Nostr utility functions.
"""

from os import getenv
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from agentstr import EventId, Keys, NostrClient, PublicKey, generate_and_save_keys

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
    # keys = generate_and_save_keys(env_var=ENV_KEY, env_path=script_dir / ".env")
    print("No private key found!")
else:
    keys = Keys.parse(NSEC)
    print(f"Private Key: {keys.secret_key().to_bech32()}")
    print(f"Public Key: {keys.public_key().to_bech32()}")

# event_list: List[str] = [
#     "1a5c33f81eb7908668445736e8075b885df1e376fa479b2132da6e0c09fb5621"
# ]

nostr_client = NostrClient(relay=RELAY, nsec=keys.secret_key().to_bech32())

# for event in event_list:
#     event_id = EventId.parse(event)
#     event = nostr_client.delete_event(event_id)
#     print(event)

marketplace_owner = PublicKey.parse(
    "npub1nar4a3vv59qkzdlskcgxrctkw9f0ekjgqaxn8vd0y82f9kdve9rqwjcurn"
)

marketplace = nostr_client.retrieve_marketplace(
    owner=marketplace_owner,
    name="Historic Downtown Snoqualmie",
)

print(f"Marketplace: {marketplace}")

for seller in marketplace:
    print(f"Seller name: {seller.name}")
    print(f"Seller about: {seller.about}")
    print(f"Seller picture: {seller.picture}")
    print(f"Seller banner: {seller.banner}")
    print(f"Seller website: {seller.website}")
