"""
Nostr utility functions.
"""

from os import getenv
from pathlib import Path
from sys import exit

from dotenv import load_dotenv

from synvya_sdk import NostrClient, NostrKeys, Profile

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
    print(f"Public Key (bech32): {keys.get_public_key()}")
    print(f"Public Key (hex): {keys.get_public_key(encoding='hex')}")

# event_list: List[str] = [
#     "1a5c33f81eb7908668445736e8075b885df1e376fa479b2132da6e0c09fb5621"
# ]

# nostr_client = NostrClient(relay=RELAY, private_key=NSEC)

# ABOUT = (
#     "Welcome to the Northwest Railway Museum where you can experience "
#     "how The Railway Changed Everything"
# )

# BANNER = "https://i.nostr.build/seoK5FZi5VCC7nXO.jpg"
# DISPLAY_NAME = "Northwest Railway Museum"
# NAME = "nrm"
# NIP05 = "nrm@synvya.com"
# PICTURE = "https://i.nostr.build/eZvrJNK9kFni5QR3.jpg"
# WEBSITE = "https://trainmuseum.org"

# profile = Profile(keys.get_public_key())
# profile.set_about(ABOUT)
# profile.set_banner(BANNER)
# profile.set_display_name(DISPLAY_NAME)
# profile.set_name(NAME)
# profile.set_nip05(NIP05)
# profile.set_picture(PICTURE)
# profile.set_website(WEBSITE)

# nostr_client.set_profile(profile)
# nostr_client.publish_profile()

# for event in event_list:
#     event_id = EventId.parse(event)
#     event = nostr_client.delete_event(event_id)
#     print(event)


# marketplace = nostr_client.retrieve_marketplace_merchants(
#     owner="npub1nar4a3vv59qkzdlskcgxrctkw9f0ekjgqaxn8vd0y82f9kdve9rqwjcurn",
#     marketplace_name="Historic Downtown Snoqualmie",
# )

# print(f"Marketplace: {marketplace}")

# for seller in marketplace:
#     print(f"Seller name: {seller.name}")
#     print(f"Seller about: {seller.about}")
#     print(f"Seller picture: {seller.picture}")
#     print(f"Seller banner: {seller.banner}")
#     print(f"Seller website: {seller.website}")
