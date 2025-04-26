"""
Nostr utility functions.
"""

import asyncio
import logging
import sys
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from synvya_sdk import (
    Namespace,
    NostrClient,
    NostrKeys,
    Profile,
    ProfileFilter,
    ProfileType,
)


async def main() -> None:
    ENV_KEY = "NOSTR_UTILS_KEY"

    # Get directory where the script is located
    script_dir = Path(__file__).parent
    # Load .env from the script's directory
    load_dotenv(script_dir / ".env")

    ENV_RELAY = "RELAY"
    DEFAULT_RELAY = "wss://nos.lol"

    # Load or use default relay
    RELAY = getenv(ENV_RELAY)
    if RELAY is None:
        RELAY = DEFAULT_RELAY

    # Load or generate keys
    NSEC = getenv(ENV_KEY)
    if NSEC is None:
        print("No private key found!")
        sys.exit(1)

    keys = NostrKeys.from_private_key(NSEC)
    print(f"Private Key: {keys.get_private_key()}")
    print(f"Public Key (bech32): {keys.get_public_key()}")
    print(f"Public Key (hex): {keys.get_public_key(encoding='hex')}")

    ABOUT = (
        "Welcome to the Northwest Railway Museum where you can experience "
        "how The Railway Changed Everything"
    )

    BANNER = "https://i.nostr.build/seoK5FZi5VCC7nXO.jpg"
    DISPLAY_NAME = "Northwest Railway Museum"
    NAME = "nrm"
    NIP05 = "nrm@synvya.com"
    PICTURE = "https://i.nostr.build/eZvrJNK9kFni5QR3.jpg"
    WEBSITE = "https://trainmuseum.org"
    CATEGORY = ProfileType.MERCHANT_RETAIL
    NAMESPACE = Namespace.MERCHANT
    HASHTAGS = ["railway", "museum", "history"]

    profile = Profile(keys.get_public_key())
    profile.set_about(ABOUT)
    profile.set_banner(BANNER)
    profile.set_display_name(DISPLAY_NAME)
    profile.set_name(NAME)
    profile.set_nip05(NIP05)
    profile.set_picture(PICTURE)
    profile.set_website(WEBSITE)
    profile.set_profile_type(CATEGORY)
    profile.set_namespace(NAMESPACE)
    for hashtag in HASHTAGS:
        profile.add_hashtag(hashtag)

    # Pass relay as a list for the new multi-relay API
    relays = [RELAY]
    nostr_client = await NostrClient.create(relays=relays, private_key=NSEC)
    nostr_client.set_logging_level(logging.DEBUG)
    await nostr_client.async_set_profile(profile)

    # try:
    #     # Continuously receive messages until interrupted
    #     while True:
    #         response = await nostr_client.async_receive_message(30)
    #         response_data = json.loads(response)

    #         # Only print if a message was received
    #         if response_data["type"] != "none":
    #             print("\n=== New Message Received ===")
    #             print(f"Type: {response_data['type']}")
    #             print(f"From: {response_data['sender']}")
    #             print(f"Content: {response_data['content']}")
    #             print("===========================\n")
    #         else:
    #             # Just print a dot to show it's still running
    #             print(".", end="", flush=True)

    # except KeyboardInterrupt:
    #     print("\nShutting down...")
    # except Exception as e:
    #     print(f"\nError: {e}")
    # finally:
    #     # Clean up code here if needed
    #     print("Goodbye!")

    # Create the ProfileFilter
    profile_filter = ProfileFilter(
        namespace=Namespace.MERCHANT,
        profile_type=ProfileType.MERCHANT_RETAIL,
        hashtags=["hardware"],
    )

    merchants: set[Profile] = await nostr_client.async_get_merchants(profile_filter)
    print(f"Number of merchants: {len(merchants)}")
    for merchant in merchants:
        print(f"Merchant: {merchant.get_display_name()}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
