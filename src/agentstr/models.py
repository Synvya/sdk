import json
import logging
from typing import List, Optional

from nostr_sdk import (
    Keys,
    Metadata,
    ProductData,
    ShippingCost,
    ShippingMethod,
    StallData,
)
from pydantic import BaseModel, ConfigDict, Field

# __all__ = [
#     "Profile",
#     "Product",
#     "Stall",
# ]


class Profile:
    """
    Nostr Profile class.
    Contains public key only.
    """

    PROFILE_URL_PREFIX: str = "https://primal.net/p/"
    logger = logging.getLogger("PublicProfile")

    def __init__(self, public_key: str) -> None:
        self.about = ""
        self.banner = ""
        self.bot = False  # future use
        self.display_name = ""
        self.locations: set[str] = set()
        self.name = ""
        self.picture = ""
        self.profile_url = self.PROFILE_URL_PREFIX + public_key
        self.public_key = public_key
        self.website = ""

        # Initialize the locations set here, per-instance

    def add_location(self, location: str) -> None:
        """Add a location to the Nostr profile.

        Args:
            location: location to add
        """
        self.locations.add(location)

    def get_about(self) -> str:
        return self.about

    def get_banner(self) -> str:
        return self.banner

    def get_display_name(self) -> str:
        return self.display_name

    def get_locations(self) -> set[str]:
        """Get the locations of the Nostr profile.

        Returns:
            set[str]: set with locations of the Nostr profile
        """
        return self.locations

    def get_name(self) -> str:
        return self.name

    def get_picture(self) -> str:
        return self.picture

    def get_profile_url(self) -> str:
        return self.profile_url

    def get_public_key(self) -> str:
        """Get the public key of the Nostr profile.

        Returns:
            str: bech32 encoded public key of the Nostr profile
        """
        return self.public_key

    def get_website(self) -> str:
        return self.website

    def is_bot(self) -> bool:
        return self.bot

    def set_about(self, about: str) -> None:
        self.about = about

    def set_banner(self, banner: str) -> None:
        self.banner = banner

    def set_bot(self, bot: bool) -> None:
        self.bot = bot

    def set_display_name(self, display_name: str) -> None:
        self.display_name = display_name

    def set_name(self, name: str) -> None:
        self.name = name

    def set_picture(self, picture: str) -> None:
        self.picture = picture

    def set_website(self, website: str) -> None:
        self.website = website

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the PublicProfile.

        Returns:
            dict: dictionary representation of the PublicProfile
        """
        return {
            "profile_url": self.profile_url,
            "public_key": self.public_key,
            "locations": list(self.locations),  # Convert set to list
            "name": self.name,
            "display_name": self.display_name,
            "about": self.about,
            "banner": self.banner,
            "picture": self.picture,
            "website": self.website,
            "bot": self.bot,
        }

    def to_json(self) -> str:
        data = {
            "name": self.name,
            "display_name": self.display_name,
            "about": self.about,
            "banner": self.banner,
            "picture": self.picture,
            "website": self.website,
            "profile_url": self.profile_url,
            "public_key": self.public_key,
            "locations": (
                list(self.locations) if self.locations else []
            ),  # Convert set to list
            "bot": str(self.bot),
        }
        return json.dumps(data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Profile):
            return False
        return str(self.public_key) == str(other.public_key)

    def __hash__(self) -> int:
        return hash(str(self.public_key))

    @classmethod
    def from_metadata(cls, metadata: Metadata, public_key: str) -> "Profile":
        profile = cls(public_key)
        profile.set_about(metadata.get_about())
        profile.set_banner(metadata.get_banner())
        profile.set_display_name(metadata.get_display_name())
        profile.set_name(metadata.get_name())
        profile.set_picture(metadata.get_picture())
        profile.set_website(metadata.get_website())
        return profile


class NostrKeys(BaseModel):
    """
    NostrKeys is a class that contains a public and private key
    in bech32 format.
    """

    public_key: str
    private_key: str

    def __init__(self, public_key: str, private_key: str) -> None:
        super().__init__(public_key=public_key, private_key=private_key)
        self.public_key = public_key
        self.private_key = private_key

    def get_public_key(self) -> str:
        """Get the public key."""
        return self.public_key

    def get_private_key(self) -> str:
        """Get the private key."""
        return self.private_key

    def to_json(self) -> str:
        """Returns a JSON representation of the NostrKeys object."""
        return json.dumps(self.to_dict())

    def __str__(self) -> str:
        """Return a string representation of the NostrKeys object."""
        return f"Public_key: {self.public_key} \nPrivate_key: {self.private_key}"

    @classmethod
    def from_private_key(cls, private_key: str) -> "NostrKeys":
        """Create a NostrKeys object from a private key."""
        keys = Keys.parse(private_key)
        return cls(keys.public_key().to_bech32(), private_key)

    @classmethod
    def parse(cls, private_key: str) -> str:
        """
        Class method to parse a private key and return a public key in bech32 format.
        """
        return Keys.parse(private_key).public_key().to_bech32()


class ProductShippingCost(BaseModel):
    psc_id: str
    psc_cost: float

    def __init__(self, psc_id: str, psc_cost: float) -> None:
        super().__init__(psc_id=psc_id, psc_cost=psc_cost)
        self.psc_id = psc_id
        self.psc_cost = psc_cost

    def get_id(self) -> str:
        return self.psc_id

    def get_cost(self) -> float:
        return self.psc_cost

    def set_id(self, psc_id: str) -> None:
        self.psc_id = psc_id

    def set_cost(self, psc_cost: float) -> None:
        self.psc_cost = psc_cost

    def to_dict(self) -> dict:
        return {"id": self.psc_id, "cost": self.psc_cost}

    def to_json(self) -> str:
        """Returns a JSON representation of the ProductShippingCost object."""
        return json.dumps(self.to_dict())

    def __str__(self) -> str:
        return f"ID: {self.psc_id} Cost: {self.psc_cost}"


class StallShippingMethod(BaseModel):
    """
    Represents a shipping method for a stall.
    """

    ssm_id: str
    ssm_cost: float
    ssm_name: str
    ssm_regions: List[str]

    def __init__(
        self, ssm_id: str, ssm_cost: float, ssm_name: str, ssm_regions: List[str]
    ) -> None:
        super().__init__(
            ssm_id=ssm_id, ssm_cost=ssm_cost, ssm_name=ssm_name, ssm_regions=ssm_regions
        )
        self.ssm_id = ssm_id
        self.ssm_cost = ssm_cost
        self.ssm_name = ssm_name
        self.ssm_regions = ssm_regions

    def get_id(self) -> str:
        return self.ssm_id

    def get_cost(self) -> float:
        return self.ssm_cost

    def get_name(self) -> str:
        return self.ssm_name

    def get_regions(self) -> List[str]:
        return self.ssm_regions

    def set_id(self, ssm_id: str) -> None:
        self.ssm_id = ssm_id

    def set_cost(self, ssm_cost: float) -> None:
        self.ssm_cost = ssm_cost

    def set_name(self, ssm_name: str) -> None:
        self.ssm_name = ssm_name

    def set_regions(self, ssm_regions: List[str]) -> None:
        self.ssm_regions = ssm_regions

    def to_dict(self) -> dict:
        return {
            "id": self.ssm_id,
            "cost": self.ssm_cost,
            "name": self.ssm_name,
            "regions": self.ssm_regions,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __str__(self) -> str:
        return f"ID: {self.ssm_id} Cost: {self.ssm_cost} Name: {self.ssm_name} Regions: {self.ssm_regions}"


class Product(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    stall_id: str
    name: str
    description: str
    images: List[str]
    currency: str
    price: float
    quantity: int
    shipping: List[ProductShippingCost]
    categories: List[str] = Field(default_factory=list)
    specs: List[List[str]] = Field(default_factory=list)

    @classmethod
    def from_product_data(cls, product_data: "ProductData") -> "Product":
        # print(f"Raw product data specs: {product_data.specs}")  # Debug print
        shipping_costs = []
        for ship in product_data.shipping:
            if isinstance(ship, dict):
                # shipping_costs.append(ShippingCost(id=ship["id"], cost=ship["cost"]))
                shipping_costs.append(
                    ProductShippingCost(psc_id=ship["id"], psc_cost=ship["cost"])
                )
            else:
                # shipping_costs.append(ship)
                shipping_costs.append(
                    ProductShippingCost(psc_id=ship.id, psc_cost=ship.cost)
                )

        # Handle specs - ensure it's a list
        specs = []
        if product_data.specs is not None:
            if isinstance(product_data.specs, dict):
                # Convert dict to list of lists if needed
                specs = [[k, v] for k, v in product_data.specs.items()]
            elif isinstance(product_data.specs, list):
                specs = product_data.specs

        return cls(
            id=product_data.id,
            stall_id=product_data.stall_id,
            name=product_data.name,
            description=product_data.description,
            images=product_data.images,
            currency=product_data.currency,
            price=product_data.price,
            quantity=product_data.quantity,
            shipping=shipping_costs,
            categories=(
                product_data.categories if product_data.categories is not None else []
            ),
            specs=specs,
        )

    def to_product_data(self) -> "ProductData":
        try:
            # Convert self.shipping from List[ProductShippingCost] to List[ShippingCost]
            shipping_costs = [
                ShippingCost(id=shipping.psc_id, cost=shipping.psc_cost)
                for shipping in self.shipping
            ]

            return ProductData(
                id=self.id,
                stall_id=self.stall_id,
                name=self.name,
                description=self.description,
                images=self.images,
                currency=self.currency,
                price=self.price,
                quantity=self.quantity,
                shipping=shipping_costs,  # Use the converted shipping costs
                categories=self.categories,
                specs=self.specs,
            )
        except Exception as e:
            logging.error("Failed to convert to ProductData: %s", e)
            logging.error("Shipping data: %s", self.shipping)
            raise

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the Product.

        Returns:
            dict: dictionary representation of the Product
        """
        # Use the to_dict method of ProductShippingCost for serialization
        shipping_dicts = [
            {"id": shipping.psc_id, "cost": shipping.psc_cost}
            for shipping in self.shipping
        ]

        return {
            "id": self.id,
            "stall_id": self.stall_id,
            "name": self.name,
            "description": self.description,
            "images": self.images,
            "currency": self.currency,
            "price": self.price,
            "quantity": self.quantity,
            "shipping": shipping_dicts,  # Use the serialized shipping costs
            "categories": self.categories,
            "specs": self.specs,
        }


class Stall(BaseModel):
    """
    Stall represents a NIP-15 stall.
    TBD: NIP-15 does not have a geohash field. Add logic to retrieve geohash from
    somewhere else when using the from_stall_data() class constructor.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    name: str
    description: str
    currency: str
    shipping: List[StallShippingMethod]
    geohash: Optional[str] = None

    # @classmethod
    # def from_stall_data(cls, stall: "StallData") -> "MerchantStall":
    #     # Create a list of StallShippingMethod from the shipping methods in StallData
    #     shipping_methods = [
    #         StallShippingMethod(
    #             ssm_id=shipping_method.get_shipping_cost().get_id(),
    #             ssm_cost=shipping_method.get_shipping_cost().get_cost(),
    #             ssm_name=shipping_method.get_name(),
    #             ssm_regions=shipping_method.get_regions(),
    #         )
    #         for shipping_method in stall.shipping()  # Assuming stall.shipping() returns a list of ShippingMethod
    #     ]

    #     return cls(
    #         id=stall.id(),
    #         name=stall.name(),
    #         description=stall.description(),
    #         currency=stall.currency(),
    #         # shipping=stall.shipping(),
    #         shipping=shipping_methods,  # Use the newly created list of StallShippingMethod
    #     )

    def get_geohash(self) -> str:
        return self.geohash

    def set_geohash(self, geohash: str) -> None:
        self.geohash = geohash

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the Stall.


        Returns:
            dict: dictionary representation of the Stall
        """
        # Use the to_dict method of StallShippingMethod for serialization
        shipping_dicts = [shipping.to_dict() for shipping in self.shipping]

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "currency": self.currency,
            "shipping": shipping_dicts,  # Use the serialized shipping methods
            "geohash": self.geohash,
        }

    def to_stall_data(self) -> "StallData":
        # Convert self.shipping from List[StallShippingMethod] to List[ShippingMethod]
        shipping_methods = [
            ShippingMethod(id=shipping.ssm_id, cost=shipping.ssm_cost)
            .name(shipping.ssm_name)
            .regions(shipping.ssm_regions)
            for shipping in self.shipping
        ]

        return StallData(
            self.id,
            self.name,
            self.description,
            self.currency,
            # self.shipping,  # No conversion needed
            shipping_methods,
        )

    @classmethod
    def from_json(cls, stall_content: str) -> "Stall":
        """
        Create a Stall instance from a JSON string.

        Args:
            stall_content (str): JSON string containing stall information.

        Returns:
            Stall: An instance of Stall.
        """
        # Parse the JSON string into a dictionary
        data = json.loads(stall_content)

        # Create a list of StallShippingMethod from the shipping data
        shipping_methods = [
            StallShippingMethod(
                ssm_id=shipping["id"],
                ssm_cost=shipping["cost"],
                ssm_name=shipping["name"],
                ssm_regions=shipping["regions"],
            )
            for shipping in data["shipping"]
        ]

        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            currency=data["currency"],
            shipping=shipping_methods,  # Use the newly created list of StallShippingMethod
        )
