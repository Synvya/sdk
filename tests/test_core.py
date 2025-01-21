import pytest, pytest_asyncio, asyncio
import logging
from dotenv import load_dotenv
from os import getenv

from phi.model.openai import OpenAIChat
from nostr_sdk import Keys, Client, SendEventOutput

from agentstr.nostr import NostrClient
from agentstr.marketplace import MerchantProfile, Merchant


# Clear existing handlers and set up logging again
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,  # Adjust to the desired level (e.g., INFO, DEBUG)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
)

load_dotenv()

def test_create_merchant_profile():
    nsec = getenv("NSEC_KEY")

    if nsec:
        merchant_profile = MerchantProfile("Synvya Inc",
                                           "Agentic communications",
                                           "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png",
                                           nsec)
        merchant_profile.merchant_profile_to_str()
        assert isinstance(merchant_profile, MerchantProfile)
        del merchant_profile
    else:
        logging.error("NSEC_KEY environment variable not set")
        assert False
        del merchant_profile

def test_publish_merchant_profile():
    nsec = getenv("NSEC_KEY")

    if nsec:
        merchant_profile = MerchantProfile(
            "Synvya Inc",
            "Agentic communications",
            "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png",
            nsec
        )
        merchant = Merchant(merchant_profile, "wss://relay.damus.io")
        eventid = merchant.publish_merchant_profile()
        assert isinstance(eventid, str)
        logging.info(f"Merchant profile published with event id: " + eventid)
        del merchant_profile
    else:
        logging.error("NSEC_KEY environment variable not set")
        assert False
        del merchant_profile

@pytest.mark.asyncio
async def test_async_publish_merchant_profile():
    nsec = getenv("NSEC_KEY")

    if nsec:
        merchant_profile = MerchantProfile(
            "Synvya Inc",
            "Agentic communications",
            "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png",
            nsec
        )
        merchant = Merchant(merchant_profile, "wss://relay.damus.io")
        eventid = await merchant._async_publish_merchant_profile()
        assert isinstance(eventid, str)
        logging.info(f"Merchant profile published with event id: " + eventid)
        del merchant_profile
    else:
        logging.error("NSEC_KEY environment variable not set")
        assert False
        del merchant_profile