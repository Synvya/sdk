import logging, hashlib, random, string
from dotenv import load_dotenv
from os import getenv
from typing import List, Tuple

import agentstr.nostr

# Clear existing handlers and set up logging again
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,  # Adjust to the desired level (e.g., INFO, DEBUG)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
)

load_dotenv()

def generate_random_id(input_str: str, length: int = 8) -> str:
    """
    Generate a random ID using a string as input.

    Args:
        input_str (str): The input string to base the ID on.
        length (int): The desired length of the random ID (default is 16).

    Returns:
        str: A random ID based on the input string.
    """
    # Step 1: Hash the input string
    hash_object = hashlib.sha256(input_str.encode())
    hash_digest = hash_object.hexdigest()  # Produces a hexadecimal string

    # Step 2: Add randomness to ensure uniqueness
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    # Step 3: Combine the hash and random part
    random_id = f"{hash_digest[:length // 2]}{random_part[:length // 2]}"

    return random_id

TEST_RELAY = "wss://relay.damus.io"

SHIPPING_ZONE_1_NAME = "North America"
SHIPPING_ZONE_1_ID = "64be11rM"
SHIPPING_ZONE_1_REGIONS = ["Canada", "Mexico", "USA"]

SHIPPING_ZONE_2_NAME = "Rest of the World"
SHIPPING_ZONE_2_ID = "d041HK7s"
SHIPPING_ZONE_2_REGIONS = ["All other countries"]

SHIPPING_ZONE_3_NAME = "Worldwide"
SHIPPING_ZONE_3_ID = "R8Gzz96K"
SHIPPING_ZONE_3_REGIONS = ["Worldwide"]

STALL_1_NAME = "The Hardware Store"
STALL_1_ID = "212au4Pi" #"212a26qV"
STALL_1_DESCRIPTION = "Your neighborhood hardware store, now available online."
STALL_1_CURRENCY = "Sats"

STALL_2_NAME = "The Trade School"
STALL_2_ID = "c8762EFD"
STALL_2_DESCRIPTION = "Educational videos to put all your hardware supplies to good use."
STALL_2_CURRENCY = "Sats"

PRODUCT_1_NAME = "Wrench"
PRODUCT_1_ID = "bcf00Rx7"
PRODUCT_1_DESCRIPTION = "The perfect tool for a $5 wrench attack."
PRODUCT_1_IMAGES = ["https://i.nostr.build/BddyYILz0rjv1wEY.png"]
PRODUCT_1_CURRENCY = STALL_1_CURRENCY
PRODUCT_1_PRICE = 5000
PRODUCT_1_QUANTITY = 100


# --*-- Define Shipping zones aka shipping methods
shipping_method_1 = agentstr.nostr.ShippingMethod(
    id= SHIPPING_ZONE_1_ID,
    cost=10000
).name(SHIPPING_ZONE_1_NAME).regions(SHIPPING_ZONE_1_REGIONS)

shipping_method_2 = agentstr.nostr.ShippingMethod(
    id= SHIPPING_ZONE_2_ID,
    cost=20000
).name(SHIPPING_ZONE_2_NAME).regions(SHIPPING_ZONE_2_REGIONS)

shipping_method_3 = agentstr.nostr.ShippingMethod(
    id= SHIPPING_ZONE_3_ID,
    cost=0
).name(SHIPPING_ZONE_3_NAME).regions(SHIPPING_ZONE_3_REGIONS)

# --*-- define Shipping costs for products. Added to cost for shipping zone 1
shipping_cost_1= agentstr.nostr.ShippingCost(
    id = SHIPPING_ZONE_1_ID,
    cost=5000
)

shipping_cost_2= agentstr.nostr.ShippingCost(
    id = SHIPPING_ZONE_2_ID,
    cost=5000
)


# --*-- define stalls
test_stall_1 = agentstr.nostr.StallData(
    id = STALL_1_ID,
    name = STALL_1_NAME,
    description = STALL_1_DESCRIPTION,
    currency = STALL_1_CURRENCY,
    shipping = [shipping_method_1, shipping_method_2]
)

test_stall_2 = agentstr.nostr.StallData(
    id = STALL_2_ID,
    name = STALL_2_NAME,
    description = STALL_2_DESCRIPTION,
    currency = STALL_2_CURRENCY,
    shipping = [shipping_method_3]
)

test_product_1 = agentstr.nostr.ProductData(
    id = PRODUCT_1_ID,
    stall_id = STALL_1_ID,
    name = PRODUCT_1_NAME,
    description = PRODUCT_1_DESCRIPTION,
    images = PRODUCT_1_IMAGES,
    currency = PRODUCT_1_CURRENCY,
    price = PRODUCT_1_PRICE,
    quantity = PRODUCT_1_QUANTITY,
    shipping = [shipping_cost_1, shipping_cost_2],
    specs= None,
    categories=None
)

# EVENT_TO_DELETE = "b0a98464f624f857035385d285105270e77ed930aa5e0bd7fe4d5e60add8db74"
events_to_delete: List[agentstr.nostr.EventId] = []

def test_publish_stall():
        
    # retrieve NSEC for tests
    nsec = getenv("NSEC_KEY")
    assert nsec, "NSEC_KEY environment variable not set"

    # create a Nostr client and connect to a relay
    # exit if failed to connect
    nostr_client = agentstr.nostr.NostrClient(TEST_RELAY, nsec)
        
    # publish the stall information
    # exit if failed to connect
    try:
        event_id = nostr_client.publish_stall(test_stall_1)
        events_to_delete.append(event_id)
        assert True
    except Exception as e:
        assert False, "Exception publishing stall " + str(test_stall_1) + ". : " + str(e)     
 

def test_publish_product():

    # retrieve NSEC for tests
    nsec = getenv("NSEC_KEY")
    assert nsec, "NSEC_KEY environment variable not set"

    # create a Nostr client and connect to a relay
    # exit if failed to connect
    nostr_client = agentstr.nostr.NostrClient(TEST_RELAY, nsec)
    
    # publish the stall information
    # exit if failed to connect
    try:
        event_id = nostr_client.publish_product(test_product_1)
        events_to_delete.append(event_id)
        assert True
    except Exception as e:
        assert False, "Exception publishing product " + str(test_product_1) + ". : " + str(e)    

def test_delete_test_events():
    # retrieve NSEC for tests
    nsec = getenv("NSEC_KEY")
    assert nsec, "NSEC_KEY environment variable not set"

    #create a Nostr client and connect to a relay
    # exit if failed to connect
    nostr_client = agentstr.nostr.NostrClient(TEST_RELAY, nsec)
    
    
    # --*-- use code below to delete an specific event for cleanup
    # event_to_delete = agentstr.nostr.EventId.parse(EVENT_TO_DELETE)
    # --*--

    # iterate through events to delete

    for event_to_delete in events_to_delete:
        try:
            # we don't care about the returned EventId
            nostr_client.delete_event(event_to_delete, "deleting the event")
        except Exception as e:
            assert False, "Failure deleting the event" 
    
    assert True