## --*-- NorthWest Railway Museum Profile Sample Data --*--
################

from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from agentstr.models import AgentProfile, MerchantProduct, MerchantStall
from agentstr.nostr import Keys, ShippingCost, ShippingMethod, generate_and_save_keys

ENV_KEY = "NRM_AGENT_KEY"

# Get directory where the script is located
script_dir = Path(__file__).parent
# Load .env from the script's directory
load_dotenv(script_dir / ".env")

# Load or generate keys
nsec = getenv(ENV_KEY)
if nsec is None:
    keys = generate_and_save_keys(env_var=ENV_KEY, env_path=script_dir / ".env")
else:
    keys = Keys.parse(nsec)

# --*-- Merchant info
NRM_NAME = "Northwest Railway Museum"
NRM_DESCRIPTION = "Welcome to the Northwest Railway Museum where you can experience how The Railway Changed Everything"
NRM_PICTURE = "https://trainmuseum.org/wp-content/uploads/2023/08/nrm-logo.png"
NRM_CURRENCY = "USD"
NRM_GEOHASH = "C23Q7U36W"

# --*-- Stall for ride at 11am
NRM_STALL_NAME = "Ride the Train"
NRM_STALL_ID = "312au4Pi"  # "212a26qV"
NRM_STALL_DESCRIPTION = """
Welcome to the Northwest Railway Museum where you can experience 
how The Railway Changed Everything. Snoqualmie Depot & Bookstore 
open 10am-5pm, 7 days a week (closed Christmas and New Years Day). 
No cost to visit the Depot and grounds. 

Ride the Snoqualmie Valley Railroad aboard historic coaches through the Upper Snoqualmie
Valley along 5.5 miles of the original 1880s Seattle, Lake Shore and Eastern Railway line.
Enjoy a 2-hour round trip excursion from either Snoqualmie Depot or North Bend Depot.
Continue west to the top of Snoqualmie Falls, a sacred site of the Snoqualmie People,
for a one-of-a-kind view of the scenic river valley. Then, head back through town for a
30-minute visit to the Railway History Campus and the Train Shed Exhibit Hall. Then, 
hop back on board to return to your starting depot to complete your round trip.

Winter Schedule: Saturdays, February-March
Summer Schedule: Saturdays and Sundays, April through September
Fall Schedule:
 - Halloween Train last three Saturdays and Sundays in October
 - Steam Weekend first Saturday and Sunday in November
 - Saturday Diesel Excursions mid-month weekends in November
 - Santa Trains last weekend in November

Snoqualmie Depot Departure from 38625 SE King Street, Snoqualmie, WA 98065
North Bend Depot Departure from 300 Railroad Ave N, North Bend, WA 98045

Departures from Snoqualmie Depot: 11am, 1pm, 3pm
Departures from North Bend Depot: 10.30am, 12.30pm, 2.30pm

Address:38625 SE King Street, Snoqualmie, WA 98065
""".strip()

# --*-- Shipping info
NRM_SHIPPING_ZONE_NAME = "Worldwide"
NRM_SHIPPING_ZONE_ID = "74be11rN"
NRM_SHIPPING_ZONE_REGIONS = ["Pickup tickets at the Will Call window at the Depot"]

# --*-- NRM Product info
NRM_PRODUCT_IMAGE = "https://shop.trainmuseum.org/ItemImages/E1000066_1.jpg"
NRM_QUANTITY = 90

NRM_ADULT_NAME = "Ride the Train Adult Ticket"
NRM_ADULT_ID = "ccf00Rx10"
NRM_ADULT_DESCRIPTION = "Ages 13 and up."
NRM_ADULT_PRICE = 28

NRM_CHILD_NAME = "Ride the Train Child Ticket"
NRM_CHILD_ID = "ccf00Rx11"
NRM_CHILD_DESCRIPTION = "Ages 2 to 12"
NRM_CHILD_PRICE = 14

NRM_SENIOR_NAME = "Ride the Train Senior Ticket"
NRM_SENIOR_ID = "ccf00Rx12"
NRM_SENIOR_DESCRIPTION = "Ages 62 and up"
NRM_SENIOR_PRICE = 24

# --*-- Define Shipping methods for stalls (nostr SDK type)
shipping_method_nrm = (
    ShippingMethod(id=NRM_SHIPPING_ZONE_ID, cost=0)
    .name(NRM_SHIPPING_ZONE_NAME)
    .regions(NRM_SHIPPING_ZONE_REGIONS)
)

# --*-- Define Shipping costs for products (nostr SDK type)
shipping_cost_nrm = ShippingCost(id=NRM_SHIPPING_ZONE_ID, cost=0)

# --*-- define stalls (using ShippingMethod)
nrm_stall = MerchantStall(
    id=NRM_STALL_ID,
    name=NRM_STALL_NAME,
    description=NRM_STALL_DESCRIPTION,
    currency=NRM_CURRENCY,
    shipping=[shipping_method_nrm],
    geohash=NRM_GEOHASH,
)

# --*-- define products (using ShippingZone)
nrm_11am_adult_ticket = MerchantProduct(
    id=NRM_ADULT_ID + "_11am",
    stall_id=NRM_STALL_ID,
    name=NRM_ADULT_NAME + " 11am",
    description=NRM_ADULT_DESCRIPTION,
    images=[NRM_PRODUCT_IMAGE],
    currency=NRM_CURRENCY,
    price=NRM_ADULT_PRICE,
    quantity=NRM_QUANTITY,
    shipping=[shipping_cost_nrm],
    categories=None,
    specs=[],
)

nrm_1pm_adult_ticket = MerchantProduct(
    id=NRM_ADULT_ID + "_1pm",
    stall_id=NRM_STALL_ID,
    name=NRM_ADULT_NAME + " 1pm",
    description=NRM_ADULT_DESCRIPTION,
    images=[NRM_PRODUCT_IMAGE],
    currency=NRM_CURRENCY,
    price=NRM_ADULT_PRICE,
    quantity=NRM_QUANTITY,
    shipping=[shipping_cost_nrm],
    categories=None,
    specs=[],
)

nrm_3pm_adult_ticket = MerchantProduct(
    id=NRM_ADULT_ID + "_3pm",
    stall_id=NRM_STALL_ID,
    name=NRM_ADULT_NAME + " 3pm",
    description=NRM_ADULT_DESCRIPTION,
    images=[NRM_PRODUCT_IMAGE],
    currency=NRM_CURRENCY,
    price=NRM_ADULT_PRICE,
    quantity=NRM_QUANTITY,
    shipping=[shipping_cost_nrm],
    categories=None,
    specs=[],
)
nrm_11am_child_ticket = MerchantProduct(
    id=NRM_CHILD_ID + "_11am",
    stall_id=NRM_STALL_ID,
    name=NRM_CHILD_NAME + " 11am",
    description=NRM_CHILD_DESCRIPTION,
    images=[NRM_PRODUCT_IMAGE],
    currency=NRM_CURRENCY,
    price=NRM_CHILD_PRICE,
    quantity=NRM_QUANTITY,
    shipping=[shipping_cost_nrm],
    categories=None,
    specs=[],
)

nrm_1pm_child_ticket = MerchantProduct(
    id=NRM_CHILD_ID + "_1pm",
    stall_id=NRM_STALL_ID,
    name=NRM_CHILD_NAME + " 1pm",
    description=NRM_CHILD_DESCRIPTION,
    images=[NRM_PRODUCT_IMAGE],
    currency=NRM_CURRENCY,
    price=NRM_CHILD_PRICE,
    quantity=NRM_QUANTITY,
    shipping=[shipping_cost_nrm],
    categories=None,
    specs=[],
)

nrm_3pm_child_ticket = MerchantProduct(
    id=NRM_CHILD_ID + "_3pm",
    stall_id=NRM_STALL_ID,
    name=NRM_CHILD_NAME + " 3pm",
    description=NRM_CHILD_DESCRIPTION,
    images=[NRM_PRODUCT_IMAGE],
    currency=NRM_CURRENCY,
    price=NRM_CHILD_PRICE,
    quantity=NRM_QUANTITY,
    shipping=[shipping_cost_nrm],
    categories=None,
    specs=[],
)

nrm_11am_senior_ticket = MerchantProduct(
    id=NRM_SENIOR_ID + "_11am",
    stall_id=NRM_STALL_ID,
    name=NRM_SENIOR_NAME + " 11am",
    description=NRM_SENIOR_DESCRIPTION,
    images=[NRM_PRODUCT_IMAGE],
    currency=NRM_CURRENCY,
    price=NRM_SENIOR_PRICE,
    quantity=NRM_QUANTITY,
    shipping=[shipping_cost_nrm],
    categories=None,
    specs=[],
)

nrm_1pm_senior_ticket = MerchantProduct(
    id=NRM_SENIOR_ID + "_1pm",
    stall_id=NRM_STALL_ID,
    name=NRM_SENIOR_NAME + " 1pm",
    description=NRM_SENIOR_DESCRIPTION,
    images=[NRM_PRODUCT_IMAGE],
    currency=NRM_CURRENCY,
    price=NRM_SENIOR_PRICE,
    quantity=NRM_QUANTITY,
    shipping=[shipping_cost_nrm],
    categories=None,
    specs=[],
)

nrm_3pm_senior_ticket = MerchantProduct(
    id=NRM_SENIOR_ID + "_3pm",
    stall_id=NRM_STALL_ID,
    name=NRM_SENIOR_NAME + " 3pm",
    description=NRM_SENIOR_DESCRIPTION,
    images=[NRM_PRODUCT_IMAGE],
    currency=NRM_CURRENCY,
    price=NRM_SENIOR_PRICE,
    quantity=NRM_QUANTITY,
    shipping=[shipping_cost_nrm],
    categories=None,
    specs=[],
)


profile = AgentProfile(keys=keys)
profile.set_name(NRM_NAME)
profile.set_about(NRM_DESCRIPTION)
profile.set_picture(NRM_PICTURE)

stalls = [nrm_stall]
products = [
    nrm_11am_adult_ticket,
    nrm_1pm_adult_ticket,
    nrm_3pm_adult_ticket,
    nrm_11am_child_ticket,
    nrm_1pm_child_ticket,
    nrm_3pm_child_ticket,
    nrm_11am_senior_ticket,
    nrm_1pm_senior_ticket,
    nrm_3pm_senior_ticket,
]
