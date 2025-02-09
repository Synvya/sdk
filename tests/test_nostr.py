import logging
import hashlib
import random
import string
import pytest
from dotenv import load_dotenv
from os import getenv
from typing import List

from agentstr.nostr import (
    NostrClient, 
    StallData, 
    ProductData, 
    ShippingMethod, 
    ShippingCost,
    EventId
)

# Configure logging
@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for all tests"""
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

@pytest.fixture(scope="session")
def nostr_client():
    """Create a NostrClient instance for tests"""
    load_dotenv()
    nsec = getenv("NSEC_TEST_KEY")
    if not nsec:
        pytest.skip("NSEC_TEST_KEY environment variable not set")
    return NostrClient("wss://relay.damus.io", nsec)

def generate_random_id(input_str: str, length: int = 8) -> str:
    """Generate a random ID using a string as input."""
    hash_object = hashlib.sha256(input_str.encode())
    hash_digest = hash_object.hexdigest()
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return f"{hash_digest[:length // 2]}{random_part[:length // 2]}"

@pytest.fixture
def shipping_methods():
    """Create shipping methods for testing"""
    method1 = ShippingMethod(
        id="64be11rM",
        cost=10000
    ).name("North America").regions(["Canada", "Mexico", "USA"])

    method2 = ShippingMethod(
        id="d041HK7s",
        cost=20000
    ).name("Rest of the World").regions(["All other countries"])

    method3 = ShippingMethod(
        id="R8Gzz96K",
        cost=0
    ).name("Worldwide").regions(["Worldwide"])

    return [method1, method2, method3]

@pytest.fixture
def shipping_costs():
    """Create shipping costs for testing"""
    return [
        ShippingCost(id="64be11rM", cost=5000),
        ShippingCost(id="d041HK7s", cost=5000)
    ]

@pytest.fixture
def test_stall(shipping_methods):
    """Create a test stall"""
    return StallData(
        id="212au4Pi",
        name="The Hardware Store",
        description="Your neighborhood hardware store, now available online.",
        currency="Sats",
        shipping=[shipping_methods[0], shipping_methods[1]]
    )

@pytest.fixture
def test_product(shipping_costs):
    """Create a test product"""
    return ProductData(
        id="bcf00Rx7",
        stall_id="212au4Pi",
        name="Wrench",
        description="The perfect tool for a $5 wrench attack.",
        images=["https://i.nostr.build/BddyYILz0rjv1wEY.png"],
        currency="Sats",
        price=5000,
        quantity=100,
        shipping=shipping_costs,
        specs=None,
        categories=None
    )

class TestNostrClient:
    """Test suite for NostrClient"""

    def test_publish_stall(self, nostr_client, test_stall):
        """Test publishing a stall"""
        event_id = nostr_client.publish_stall(test_stall)
        assert isinstance(event_id, EventId)

    def test_publish_product(self, nostr_client, test_product):
        """Test publishing a product"""
        event_id = nostr_client.publish_product(test_product)
        assert isinstance(event_id, EventId)

    def test_delete_event(self, nostr_client, test_stall):
        """Test deleting an event"""
        # First publish something to delete
        event_id = nostr_client.publish_stall(test_stall)
        assert isinstance(event_id, EventId)
        
        # Then delete it
        delete_event_id = nostr_client.delete_event(event_id, reason="Test deletion")
        assert isinstance(delete_event_id, EventId)

    def test_publish_profile(self, nostr_client):
        """Test publishing a profile"""
        event_id = nostr_client.publish_profile(
            name="Test Profile",
            about="A test profile",
            picture="https://example.com/pic.jpg"
        )
        assert isinstance(event_id, EventId)

    @pytest.mark.asyncio
    async def test_async_connect(self, nostr_client):
        """Test async connection"""
        result = await nostr_client._async_connect()
        assert result == NostrClient.SUCCESS

    def test_set_logging_level(self):
        """Test setting logging level"""
        NostrClient.set_logging_level(logging.DEBUG)
        assert NostrClient.logger.level == logging.DEBUG