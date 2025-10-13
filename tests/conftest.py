"""
This module contains the conftest file for the tests.
"""

import json
import logging
from os import getenv
from pathlib import Path
from typing import List
from unittest.mock import Mock

import pytest
from _pytest.nodes import Item
from dotenv import load_dotenv
from nostr_sdk import Event

from agno.knowledge.knowledge import Knowledge
from synvya_sdk import (
    ClassifiedListing,
    Collection,
    KeyEncoding,
    NostrKeys,
    Product,
    ProductShippingCost,
    Profile,
    Stall,
    StallShippingMethod,
    generate_keys,
)
from synvya_sdk.agno import BuyerTools, MerchantTools

# Get directory where the script is located
script_dir = Path(__file__).parent
# Load .env from the script's directory
load_dotenv(script_dir / ".env")

# Load or generate keys for test profiles


def pytest_collection_modifyitems(items: List[Item]) -> None:
    """Define the desired execution order of test files"""
    # Define the desired execution order of test files
    ordered_files = [
        "tests/test_nostr_integration.py",
        "tests/test_nostr_mocked.py",
        "tests/agno/test_seller.py",
        "tests/agno/test_buyer.py",
    ]

    # Create a dictionary mapping filenames to execution order
    order_map = {name: index for index, name in enumerate(ordered_files)}

    # Sort test items based on the order_map; default to a high value
    # for unspecified files
    items.sort(key=lambda item: order_map.get(item.location[0], 100))


@pytest.fixture(scope="session", name="relay")
def relay_fixture() -> str:
    """Fixture providing the test relay"""
    return "wss://nos.lol"


@pytest.fixture(scope="session", name="nip96_server_url")
def nip96_server_url_fixture() -> str:
    """Fixture providing the NIP-96 test server URL"""
    return "https://nostr.build"


@pytest.fixture(scope="session", name="test_file_data")
def test_file_data_fixture() -> bytes:
    """Fixture providing test file data for NIP-96 upload"""
    # Use the sample image from tests directory
    script_dir = Path(__file__).parent
    sample_image_path = script_dir / "sample_image.jpg"

    with open(sample_image_path, "rb") as f:
        return f.read()


@pytest.fixture(scope="session", name="test_file_mime_type")
def test_file_mime_type_fixture() -> str:
    """Fixture providing test file MIME type"""
    # Using JPEG since we have sample_image.jpg in tests directory
    return "image/jpeg"


###--- Merchant Fixtures ---###


@pytest.fixture(scope="session", name="merchant_keys")
def merchant_keys_fixture() -> NostrKeys:
    """Fixture providing the test merchant keys"""
    nsec = getenv("TEST_MERCHANT_KEY")
    if nsec is None:
        return generate_keys(env_var="TEST_MERCHANT_KEY", env_path=script_dir / ".env")

    return NostrKeys(private_key=nsec)


@pytest.fixture(scope="session", name="classified_merchant_keys")
def classified_merchant_keys_fixture() -> NostrKeys:
    """Fixture providing the test keys for a merchant with classified listings"""
    nsec = getenv("TEST_CLASSIFIED_MERCHANT_KEY")
    if nsec is None:
        return generate_keys(
            env_var="TEST_CLASSIFIED_MERCHANT_KEY", env_path=script_dir / ".env"
        )

    return NostrKeys(private_key=nsec)


@pytest.fixture(scope="session", name="merchant_about")
def merchant_about_fixture() -> str:
    """Fixture providing the test profile about"""
    return "A merchant test profile"


@pytest.fixture(scope="session", name="merchant_banner")
def merchant_banner_fixture() -> str:
    """Fixture providing the test profile banner"""
    return "https://i.nostr.build/ENQ6OuMhoi2L17WD.png"


@pytest.fixture(scope="session", name="merchant_bot")
def merchant_bot_fixture() -> bool:
    """Fixture providing the test profile bot"""
    return True


@pytest.fixture(scope="session", name="merchant_location")
def merchant_location_fixture() -> str:
    """Fixture providing the test location"""
    return "000000000"


@pytest.fixture(scope="session", name="merchant_name")
def merchant_name_fixture() -> str:
    """Fixture providing the test profile name"""
    return "merchant"


@pytest.fixture(scope="session", name="merchant_display_name")
def merchant_display_name_fixture() -> str:
    """Fixture providing the test profile display name"""
    return "Merchant Inc."


@pytest.fixture(scope="session", name="merchant_nip05")
def merchant_nip05_fixture() -> str:
    """Fixture providing the test profile nip_05"""
    return "merchant@synvya.com"


@pytest.fixture(scope="session", name="merchant_picture")
def merchant_picture_fixture() -> str:
    """Fixture providing the test profile picture"""
    return "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"


@pytest.fixture(scope="session", name="merchant_city")
def merchant_city_fixture() -> str:
    """Fixture providing the test profile city"""
    return "Springfield"


@pytest.fixture(scope="session", name="merchant_country")
def merchant_country_fixture() -> str:
    """Fixture providing the test profile country"""
    return "USA"


@pytest.fixture(scope="session", name="merchant_email")
def merchant_email_fixture() -> str:
    """Fixture providing the test profile email"""
    return "merchant@synvya.com"


@pytest.fixture(scope="session", name="merchant_phone")
def merchant_phone_fixture() -> str:
    """Fixture providing the test profile phone"""
    return "+15551234567"


@pytest.fixture(scope="session", name="merchant_state")
def merchant_state_fixture() -> str:
    """Fixture providing the test profile state"""
    return "IL"


@pytest.fixture(scope="session", name="merchant_street")
def merchant_street_fixture() -> str:
    """Fixture providing the test profile street"""
    return "123 Main St"


@pytest.fixture(scope="session", name="merchant_zip_code")
def merchant_zip_code_fixture() -> str:
    """Fixture providing the test profile zip code"""
    return "62704"


@pytest.fixture(scope="session", name="merchant_website")
def merchant_website_fixture() -> str:
    """Fixture providing the test profile website"""
    return "https://www.synvya.com"


@pytest.fixture(scope="session", name="merchant_profile")
def merchant_profile_fixture(
    merchant_keys: NostrKeys,
    merchant_about: str,
    merchant_banner: str,
    merchant_bot: bool,
    merchant_city: str,
    merchant_country: str,
    merchant_display_name: str,
    merchant_email: str,
    merchant_location: str,
    merchant_name: str,
    merchant_nip05: str,
    merchant_picture: str,
    merchant_phone: str,
    merchant_state: str,
    merchant_street: str,
    merchant_website: str,
    merchant_zip_code: str,
) -> Profile:
    """Fixture providing the test merchant profile"""
    profile = Profile(merchant_keys.get_public_key(KeyEncoding.BECH32))
    profile.add_location(merchant_location)
    profile.set_about(merchant_about)
    profile.set_banner(merchant_banner)
    profile.set_bot(merchant_bot)
    profile.set_city(merchant_city)
    profile.set_country(merchant_country)
    profile.set_email(merchant_email)
    profile.set_name(merchant_name)
    profile.set_display_name(merchant_display_name)
    profile.set_nip05(merchant_nip05)
    profile.set_picture(merchant_picture)
    profile.set_phone(merchant_phone)
    profile.set_state(merchant_state)
    profile.set_street(merchant_street)
    profile.set_website(merchant_website)
    profile.set_zip_code(merchant_zip_code)
    return profile


###---  Buyer Fixtures ---###


@pytest.fixture(scope="session", name="buyer_keys")
def buyer_keys_fixture() -> NostrKeys:
    """Fixture providing the test buyer keys"""
    nsec = getenv("TEST_BUYER_KEY")
    if nsec is None:
        return generate_keys(env_var="TEST_BUYER_KEY", env_path=script_dir / ".env")
    return NostrKeys(nsec)


@pytest.fixture(scope="session", name="buyer_about")
def buyer_about_fixture() -> str:
    """Fixture providing the test profile about"""
    return "A buyer test profile"


@pytest.fixture(scope="session", name="buyer_banner")
def buyer_banner_fixture() -> str:
    """Fixture providing the test profile banner"""
    return "https://i.nostr.build/EiS8XFCROnSRr17o.png"


@pytest.fixture(scope="session", name="buyer_name")
def buyer_name_fixture() -> str:
    """Fixture providing the test profile name"""
    return "Buyer Test Profile"


@pytest.fixture(scope="session", name="buyer_picture")
def buyer_picture_fixture() -> str:
    """Fixture providing the test profile picture"""
    return "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"


@pytest.fixture(scope="session", name="buyer_website")
def buyer_website_fixture() -> str:
    """Fixture providing the test profile website"""
    return "https://buyer.test"


@pytest.fixture(scope="session", name="buyer_profile")
def buyer_profile_fixture(
    buyer_keys: NostrKeys,
    buyer_about: str,
    buyer_banner: str,
    buyer_name: str,
    buyer_picture: str,
    buyer_website: str,
) -> Profile:
    """Fixture providing the test merchant profile"""
    profile = Profile(buyer_keys.get_public_key(KeyEncoding.BECH32))
    profile.set_about(buyer_about)
    profile.set_banner(buyer_banner)
    profile.set_name(buyer_name)
    profile.set_picture(buyer_picture)
    profile.set_website(buyer_website)
    return profile


@pytest.fixture(scope="session", name="profile_event_id")
def profile_event_id_fixture() -> str:
    """Fixture providing the test profile event id"""
    return "note1f8ew29sf9cdln2kf5c8eylkujgth6t06ae2vmt8k9ftjaljulmlset9qnj"


@pytest.fixture(scope="session", name="geohashs")
def geohashs_fixture() -> List[str]:
    """Fixture providing the test geohashs"""
    return ["000000000", "000000000"]


@pytest.fixture(scope="session", name="stall_shipping_methods")
def stall_shipping_methods_fixture() -> List[StallShippingMethod]:
    """Create stall shipping methods for testing"""
    return [
        StallShippingMethod(
            ssm_id="64be11rM",
            ssm_cost=10000,
            ssm_name="North America",
            ssm_regions=["Canada", "Mexico", "USA"],
        ),
        StallShippingMethod(
            ssm_id="d041HK7s",
            ssm_cost=20000,
            ssm_name="Rest of the World",
            ssm_regions=["All other countries"],
        ),
        StallShippingMethod(
            ssm_id="R8Gzz96K",
            ssm_cost=0,
            ssm_name="Worldwide",
            ssm_regions=["Worldwide"],
        ),
    ]


@pytest.fixture(scope="session", name="product_shipping_costs")
def product_shipping_costs_fixture() -> List[ProductShippingCost]:
    """Create product shipping costs for testing"""
    return [
        ProductShippingCost(psc_id="64be11rM", psc_cost=5000),
        ProductShippingCost(psc_id="d041HK7s", psc_cost=5000),
        ProductShippingCost(psc_id="R8Gzz96K", psc_cost=0),
    ]


@pytest.fixture(scope="session", name="stalls")
def stalls_fixture(
    stall_shipping_methods: List[StallShippingMethod], geohashs: List[str]
) -> List[Stall]:
    """Create Stall test fixtures"""
    return [
        Stall(
            id="212au4Pi",
            name="The Hardware Store",
            description="Your neighborhood hardware store, now available online.",
            currency="Sats",
            shipping=[stall_shipping_methods[0], stall_shipping_methods[1]],
            geohash=geohashs[0],
        ),
        Stall(
            id="212au4Ph",
            name="The Trade School",
            description="Educational videos to put all your hardware supplies to good use.",
            currency="Sats",
            shipping=[stall_shipping_methods[2]],
            geohash=geohashs[1],
        ),
    ]


@pytest.fixture(scope="session", name="stall_event_ids")
def stall_event_ids_fixture() -> List[str]:
    """Fixture providing valid but dummy hex test stall event ids"""
    return [
        "c12fed92c3dd928fcce4a5d0a5ec608aa52687f4ac45fad6ef1b4895c19fec75",
        "ecc04d51f124598abb7bd6830e169dbd4d97aef3bfc19a20ba07b99db709b893",
    ]


@pytest.fixture(scope="session", name="products")
def products_fixture(
    product_shipping_costs: List[ProductShippingCost],
    merchant_keys: NostrKeys,
) -> List[Product]:
    """Create Product test fixtures"""
    return [
        Product(
            id="bcf00Rx7",
            stall_id="212au4Pi",
            name="Wrench",
            description="The perfect tool for a $5 wrench attack.",
            images=["https://i.nostr.build/BddyYILz0rjv1wEY.png"],
            currency="Sats",
            price=5000,
            quantity=100,
            shipping=[product_shipping_costs[0], product_shipping_costs[1]],
            specs=[["length", "10cm"], ["material", "steel"]],
            categories=["hardware", "tools"],
            seller=merchant_keys.get_public_key(KeyEncoding.BECH32),
        ),
        Product(
            id="bcf00Rx8",
            stall_id="212au4Pi",
            name="Shovel",
            description="Dig yourself into a hole like never before",
            images=["https://i.nostr.build/psL0ZtN4FZcmeiIh.png"],
            currency="Sats",
            price=10000,
            quantity=10,
            shipping=[product_shipping_costs[0], product_shipping_costs[1]],
            specs=[["length", "100 cm"], ["material", "steel"]],
            categories=["hardware", "tools"],
            seller=merchant_keys.get_public_key(KeyEncoding.BECH32),
        ),
        Product(
            id="ccf00Rx1",
            stall_id="212au4Ph",
            name="Shovel 101",
            description="How to dig your own grave",
            images=["https://i.nostr.build/psL0ZtN4FZcmeiIh.png"],
            currency="Sats",
            price=1000,
            quantity=1000,
            shipping=[product_shipping_costs[2]],
            specs=[["type", "online"], ["media", "video"]],
            categories=["education", "hardware tools"],
            seller=merchant_keys.get_public_key(KeyEncoding.BECH32),
        ),
    ]


@pytest.fixture(scope="session", name="product_event_ids")
def product_event_ids_fixture() -> List[str]:
    """Fixture providing  valid but dummy hex test product event ids"""
    return [
        "d1441f3532a44772fba7c57eb7c71c94c3971246722ae6e372cf50c198af784a",
        "b6a81ca6cbd5fa59e564208796a76af670a7a402ec0bb4621c999688ed10e43e",
        "dc25ae17347de75763c7462d7b7e26011167b05a60c425e3cf9aecea753930e6",
    ]


@pytest.fixture(scope="session", name="products_in_stall_event_ids")
def products_in_stall_event_ids_fixture() -> List[str]:
    """Fixture providing  valid but dummy hex test product event ids"""
    return [
        "d1441f3532a44772fba7c57eb7c71c94c3971246722ae6e372cf50c198af784a",
        "b6a81ca6cbd5fa59e564208796a76af670a7a402ec0bb4621c999688ed10e43e",
    ]


@pytest.fixture(scope="function", name="merchant_tools")
async def merchant_tools_fixture(
    relay: str,
    merchant_keys: NostrKeys,
    stalls: List[Stall],
    products: List[Product],
) -> MerchantTools:
    """Create a merchant instance for testing"""
    from unittest.mock import AsyncMock, Mock, patch

    # Step 1: Create a proper mock client that mixes Mock and AsyncMock
    # Use a standard Mock as the base
    mock_client = Mock()

    # Replace specific methods that need to be async with AsyncMock
    mock_client.async_get_profile = AsyncMock()
    mock_client.async_get_profile.return_value = Profile(
        merchant_keys.get_public_key(KeyEncoding.BECH32)
    )
    mock_client.async_get_merchants = AsyncMock()
    mock_client.async_get_merchants_in_marketplace = AsyncMock()
    mock_client.async_get_products = AsyncMock()
    mock_client.async_get_stalls = AsyncMock()
    mock_client.async_publish_note = AsyncMock()
    mock_client.async_set_product = AsyncMock()
    mock_client.async_set_stall = AsyncMock()
    mock_client.async_set_profile = AsyncMock()
    mock_client.async_delete_event = AsyncMock()
    mock_client.async_send_message = AsyncMock()
    mock_client.async_receive_message = AsyncMock()

    # Step 2: Use patch as a context manager to replace NostrClient.create
    with patch("synvya_sdk.NostrClient.create", return_value=mock_client):
        # Step 3: Create MerchantTools instance with mocked dependencies
        # Convert relay to a list for compatibility with the updated interface
        merchant_tools = await MerchantTools.create(
            [relay], merchant_keys.get_private_key(KeyEncoding.BECH32), stalls, products
        )

        # Ensure the mocked client is properly assigned to the instance
        merchant_tools.nostr_client = mock_client

        return merchant_tools


@pytest.fixture(scope="session", name="mock_knowledge_base")
def mock_knowledge_base_fixture() -> Mock:
    """Fixture to return a mocked AgentKnowledge object."""
    return Mock(spec=Knowledge)


@pytest.fixture(scope="function", name="buyer_tools")
async def buyer_tools_fixture(
    mock_knowledge_base: Mock,
    relay: str,
    buyer_keys: NostrKeys,
    merchant_profile: Profile,
) -> BuyerTools:
    """Create a Buyer instance for testing"""
    from unittest.mock import AsyncMock, Mock, patch

    # Step 1: Create a proper mock client that mixes Mock and AsyncMock
    # Use a standard Mock as the base
    mock_client = Mock()

    # Replace specific methods that need to be async with AsyncMock
    mock_client.async_get_profile = AsyncMock()
    mock_client.async_get_profile.return_value = Profile(
        buyer_keys.get_public_key(KeyEncoding.BECH32)
    )
    mock_client.async_get_merchants = AsyncMock()
    mock_client.async_get_merchants_in_marketplace = AsyncMock()
    mock_client.async_get_products = AsyncMock()
    mock_client.async_get_stalls = AsyncMock()
    mock_client.async_send_message = AsyncMock()
    mock_client.async_receive_message = AsyncMock()

    # Step 2: Use patch as a context manager to replace NostrClient.create
    with patch("synvya_sdk.NostrClient.create", return_value=mock_client):
        # Step 3: Create BuyerTools instance with mocked dependencies
        # Convert relay to a list for compatibility with the updated interface
        buyer_tools = await BuyerTools.create(
            mock_knowledge_base,
            [relay],
            buyer_keys.get_private_key(KeyEncoding.BECH32),
        )
        # Step 4: Set merchants directly
        buyer_tools.merchants = {merchant_profile}

        # Ensure the mocked client is properly assigned to the instance
        buyer_tools._nostr_client = mock_client

        return buyer_tools


# --------------------------------------------------------------------------- #
# Classified listings fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="session", name="classified_listings")
def classified_listings_fixture() -> List[ClassifiedListing]:
    """Fixture providing classified listings parsed from examples."""
    logger = logging.getLogger(__name__)

    raw_examples = [
        {
            "id": "f9651dacbd7907b632676de1195aad81241edab2e50a522239cf12b98f5a5f32",  # pragma: allowlist secret
            "pubkey": "e01e4b0b3677204161b8d13d0a7b88e5d2e7dac2f7d2cc5530a3bc1dca3fbd2f",  # pragma: allowlist secret
            "created_at": 1760115108,
            "kind": 30402,
            "tags": [
                ["d", "sq-66ba594c38d17f0e"],
                ["title", "Cinnamon muffin (Regular)"],
                ["summary", "Delicious and gluten free cinnamon muffin"],
                ["location", "Pressed on Main"],
                [
                    "image",
                    "https://items-images-sandbox.s3.us-west-2.amazonaws.com/files/6a610d1df174af9720f4aa7014646280803f3799/original.png",
                    "",
                ],
                ["price", "4.99", "USD"],
                ["published_at", "1760115108"],
                ["t", "bakery"],
                ["t", "gluten-free"],
            ],
            "content": "**Cinnamon muffin – Regular**\n\nDelicious and gluten free cinnamon muffin\n\nSKU: N/A",
            "sig": "dabe44335f052bb76d8bb4da7292dfea6faeafa3b8fd0b371a539f7a66cdbd660487a85a335312d1eaf792c4ab0bf34e1db43c6e400786af10518436ab5841e8",  # pragma: allowlist secret
        },
        {
            "id": "c527f06c684edcd74aeba714c31d3ef1b46fad392c5c423d92087f10f29a9a0c",  # pragma: allowlist secret
            "pubkey": "e01e4b0b3677204161b8d13d0a7b88e5d2e7dac2f7d2cc5530a3bc1dca3fbd2f",  # pragma: allowlist secret
            "created_at": 1760111814,
            "kind": 30402,
            "tags": [
                ["d", "sq-c5a018329229678c"],
                ["title", "Detox Smoothie (Default)"],
                ["summary", "Start your day with a cleansing smoothie."],
                ["location", "Pressed on Main"],
                [
                    "image",
                    "https://items-images-sandbox.s3.us-west-2.amazonaws.com/files/e7c005df06d36508e5f02f8c13f5a5fecefe40b2/original.png",
                    "",
                ],
                ["price", "7.99", "USD"],
                ["published_at", "1760111814"],
                ["t", "smoothies"],
                ["t", "gluten-free"],
                ["t", "beverages"],
            ],
            "content": "**Detox Smoothie – Default**\n\nStart your day with a cleansing smoothie.\n\nSKU: N/A",
            "sig": "2997a2f1d338d913f82f9a420a27d78acdb90dcd4ef3fae130dee4d0321cccf307d50fefd3d41922c745af1b72e4f010b4481552ba53794c2d8b12d95e2a5137",  # pragma: allowlist secret
        },
        {
            "id": "402bd2b42f39d6a348d5b79784a05df485b6ddd9da4ae2574357c14023e7dc86",  # pragma: allowlist secret
            "pubkey": "e01e4b0b3677204161b8d13d0a7b88e5d2e7dac2f7d2cc5530a3bc1dca3fbd2f",  # pragma: allowlist secret
            "created_at": 1760051195,
            "kind": 30402,
            "tags": [
                ["d", "sq-298906f03c3c909a"],
                ["title", "Blueberry muffin (Regular)"],
                ["summary", "Organic, gluten-free blueberry deliciousness"],
                ["location", "Pressed on Main"],
                [
                    "image",
                    "https://items-images-sandbox.s3.us-west-2.amazonaws.com/files/b5738fd0b07b604f83e344b50184f1d842e36d50/original.png",
                    "",
                ],
                ["price", "4.49", "USD"],
                ["published_at", "1760051195"],
                ["t", "bakery"],
                ["t", "gluten-free"],
            ],
            "content": "**Blueberry muffin – Regular**\n\nOrganic, gluten-free blueberry deliciousness\n\nSKU: N/A",
            "sig": "4249fcde0c824cd0a3ad9f54e63fad5a39b3a26e7edb288c6d8038a7e6717e91bfd383277e353017e19a070b474860b4175519a6376df60c64f20247ca522ec3",  # pragma: allowlist secret
        },
        {
            "id": "7e104f5df5df28166986a0f89d89567092a2587b50055881e63be9ac578787e1",  # pragma: allowlist secret
            "pubkey": "e01e4b0b3677204161b8d13d0a7b88e5d2e7dac2f7d2cc5530a3bc1dca3fbd2f",  # pragma: allowlist secret
            "created_at": 1760051195,
            "kind": 30402,
            "tags": [
                ["d", "sq-2dc0d604926af022"],
                ["title", "Energy Smoothie (Default)"],
                [
                    "summary",
                    "Charge up your day with an energy smoothie. Perfect for a morning charge or mid-day recharge.",
                ],
                ["location", "Pressed on Main"],
                [
                    "image",
                    "https://items-images-sandbox.s3.us-west-2.amazonaws.com/files/f452dbe8c7b189220abef728343156bb351dddb6/original.png",
                    "",
                ],
                ["price", "4.99", "USD"],
                ["published_at", "1760051195"],
                ["t", "smoothies"],
                ["t", "gluten-free"],
                ["t", "beverages"],
            ],
            "content": "**Energy Smoothie – Default**\n\nCharge up your day with an energy smoothie. Perfect for a morning charge or mid-day recharge.\n\nSKU: N/A",
            "sig": "d96b17d981d6e76b71d08f4683c32bd2cf3cbd6294de68672ae969b9462a0c8d15e54fdd65cc03f21c1b2909f989e88f7294490fb45fb251345b1aa4dc94101c",  # pragma: allowlist secret
        },
    ]

    listings: List[ClassifiedListing] = []
    for record in raw_examples:
        try:
            event = Event.from_json(json.dumps(record))
            listings.append(ClassifiedListing.from_event(event))
        except (ValueError, TypeError) as exc:
            logger.warning("Skipping invalid classified listing example: %s", exc)

    if not listings:
        raise RuntimeError(
            "No classified listing examples available in classified_listings fixture"
        )

    return listings
