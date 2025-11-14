"""
Nostr utility functions.
"""

import asyncio
import logging
import sys
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from synvya_sdk import KeyEncoding, Label, Namespace, NostrClient, NostrKeys, Profile


async def test_nip96_upload(nostr_client: NostrClient) -> None:
    """
    Test NIP-96 file upload functionality.

    Args:
        nostr_client: An initialized NostrClient instance
    """
    print("\n=== Testing NIP-96 File Upload ===")

    # Path to a sample image
    script_dir = Path(__file__).parent
    sample_image_path = script_dir / "sample_image.jpg"

    if not sample_image_path.exists():
        print(f"Sample image not found at: {sample_image_path}")
        return

    # Read the image file
    try:
        with open(sample_image_path, "rb") as f:
            file_data = f.read()

        print(f"File size: {len(file_data)} bytes")

        # NIP-96 server URL (nostr.build is a popular NIP-96 compatible server)
        server_url = "https://nostr.build"

        print(f"Uploading file to {server_url}...")

        # Upload the file
        upload_url = await nostr_client.async_nip96_upload(
            server_url=server_url, file_data=file_data, mime_type="image/jpeg"
        )

        print(f"File uploaded successfully!")
        print(f"Download URL: {upload_url}")
        print(
            "You can use this URL in your Nostr events, for example, as a profile picture."
        )

    except Exception as e:
        print(f"Error during NIP-96 upload: {e}")

    print("=== NIP-96 Test Complete ===\n")


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

    keys = NostrKeys(NSEC)
    print(f"Private Key: {keys.get_private_key(encoding=KeyEncoding.BECH32)}")
    print(f"Public Key (bech32): {keys.get_public_key(encoding=KeyEncoding.BECH32)}")
    print(f"Public Key (hex): {keys.get_public_key(encoding=KeyEncoding.HEX)}")

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
    CATEGORY = Label.MUSEUM
    NAMESPACE = Namespace.SCHEMA_ORG
    HASHTAGS = ["railway", "museum", "history"]

    profile = Profile(keys.get_public_key(encoding=KeyEncoding.BECH32))
    profile.set_about(ABOUT)
    profile.set_banner(BANNER)
    profile.set_display_name(DISPLAY_NAME)
    profile.set_name(NAME)
    profile.set_nip05(NIP05)
    profile.set_picture(PICTURE)
    profile.set_website(WEBSITE)
    profile.add_label(CATEGORY, NAMESPACE)
    profile.set_city("Snoqualmie")
    profile.set_state("WA")
    profile.set_country("US")
    profile.set_zip_code("98065")
    profile.set_street("38625 SE King Street")
    profile.set_email("info@TrainMuseum.org")
    profile.set_phone("425-888-3030 ext. 7202")
    profile.set_geohash("c23q7u338")
    for hashtag in HASHTAGS:
        profile.add_hashtag(hashtag)
    profile.set_environment("demo")

    # Pass relay as a list for the new multi-relay API
    relays = [RELAY]
    nostr_client = await NostrClient.create(relays=relays, private_key=NSEC)
    nostr_client.set_logging_level(logging.DEBUG)
    await nostr_client.async_set_profile(profile)

    # Test NIP-96 file upload functionality
    # await test_nip96_upload(nostr_client)

    # # Create the ProfileFilter
    # profile_filter = ProfileFilter(
    #     namespace=Namespace.MERCHANT,
    #     profile_type=ProfileType.MERCHANT_RETAIL,
    #     hashtags=["hardware"],
    # )

    # merchants: set[Profile] = await nostr_client.async_get_merchants(profile_filter)
    # print(f"Number of merchants: {len(merchants)}")
    # for merchant in merchants:
    #     print(f"Merchant: {merchant.get_display_name()}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
