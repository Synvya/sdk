"""
Nostr utility functions.
"""

from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from synvya_sdk import NostrClient, NostrKeys

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
    print("No private key found!")
    exit(1)
else:
    keys = NostrKeys.from_private_key(NSEC)
    print(f"Private Key: {keys.get_private_key()}")
    print(f"Public Key: {keys.get_public_key()}")

# event_list: List[str] = [
#     "1a5c33f81eb7908668445736e8075b885df1e376fa479b2132da6e0c09fb5621"
# ]

nostr_client = NostrClient(relay=RELAY, private_key=NSEC)

# for event in event_list:
#     event_id = EventId.parse(event)
#     event = nostr_client.delete_event(event_id)
#     print(event)


marketplace = nostr_client.retrieve_marketplace_merchants(
    owner="npub1nar4a3vv59qkzdlskcgxrctkw9f0ekjgqaxn8vd0y82f9kdve9rqwjcurn",
    marketplace_name="Historic Downtown Snoqualmie",
)

print(f"Marketplace: {marketplace}")

for seller in marketplace:
    print(f"Seller name: {seller.name}")
    print(f"Seller about: {seller.about}")
    print(f"Seller picture: {seller.picture}")
    print(f"Seller banner: {seller.banner}")
    print(f"Seller website: {seller.website}")
