import json
import logging
from typing import List, Optional

from nostr_sdk import (
    Keys,
    Metadata,
    ProductData,
    PublicKey,
    ShippingCost,
    ShippingMethod,
    StallData,
)
from pydantic import BaseModel, ConfigDict

__all__ = [
    "Profile",
    "NostrProfile",
    "AgentProfile",
    "MerchantProduct",
    "MerchantStall",
]


class Profile:
    """
    Generic Profile class that holds the metadata of a Nostr profile.
    """

    logger = logging.getLogger("Profile")

    def __init__(self) -> None:
        self.about = ""
        self.display_name = ""
        self.name = ""
        self.picture = ""
        self.website = ""

    def get_about(self) -> str:
        return self.about

    def get_display_name(self) -> str:
        return self.display_name

    def get_name(self) -> str:
        return self.name

    def get_picture(self) -> str:
        return self.picture

    def get_website(self) -> str:
        return self.website

    def set_about(self, about: str) -> None:
        self.about = about

    def set_display_name(self, display_name: str) -> None:
        self.display_name = display_name

    def set_name(self, name: str) -> None:
        self.name = name

    def set_picture(self, picture: str) -> None:
        self.picture = picture

    def set_website(self, website: str) -> None:
        self.website = website

    def to_json(self) -> str:
        data = {
            "name": self.name,
            "display_name": self.display_name,
            "about": self.about,
            "picture": self.picture,
            "website": self.website,
        }
        return json.dumps(data)


class NostrProfile(Profile):
    """
    NostrProfile is a Profile that is used to represent a public Nostr profile.

    Key difference between NostrProfile and AgentProfile is that NostrProfile represents
    a third party profile and therefore it only has a public key.
    """

    public_key: PublicKey
    profile_url: str
    # zip_codes: List[str] = []
    WEB_URL: str = "https://primal.net/p/"
    locations: set[str] = set()

    def __init__(self, public_key: PublicKey) -> None:
        super().__init__()
        self.public_key = public_key
        self.profile_url = self.WEB_URL + self.public_key.to_bech32()

    @classmethod
    def from_metadata(cls, metadata: Metadata, public_key: PublicKey) -> "NostrProfile":
        profile = cls(public_key)
        profile.set_about(metadata.get_about())
        profile.set_display_name(metadata.get_display_name())
        profile.set_name(metadata.get_name())
        profile.set_picture(metadata.get_picture())
        profile.set_website(metadata.get_website())
        return profile

    def add_location(self, location: str) -> None:
        """Add a location to the Nostr profile.

        Args:
            location: location to add
        """
        self.locations.add(location)

    def get_public_key(self) -> str:
        """Get the public key of the Nostr profile.

        Returns:
            str: bech32 encoded public key of the Nostr profile
        """
        return str(self.public_key.to_bech32())

    def get_locations(self) -> set[str]:
        """Get the locations of the Nostr profile.

        Returns:
            set[str]: set with locations of the Nostr profile
        """
        return self.locations

    def get_profile_url(self) -> str:
        return self.profile_url

    def get_zip_codes(self) -> List[str]:
        return self.zip_codes

    def to_json(self) -> str:
        # Ensure super().to_json() returns a dictionary
        parent_json = super().to_json()
        data = json.loads(parent_json) if isinstance(parent_json, str) else parent_json

        # Add NostrProfile-specific fields
        data.update(
            {
                "profile_url": self.profile_url,
                "public_key": self.public_key.to_bech32(),
                "locations": list(
                    self.locations or []
                ),  # Ensure it's a list, even if None
            }
        )

        return json.dumps(data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NostrProfile):
            return False
        return str(self.public_key.to_bech32()) == str(other.public_key.to_bech32())

    def __hash__(self) -> int:
        return hash(str(self.public_key.to_bech32()))


class AgentProfile(Profile):
    """
    AgentProfile is a Profile that is used to represent an agent.
    """

    WEB_URL: str = "https://primal.net/p/"
    profile_url: str
    keys: Keys

    def __init__(self, keys: Keys) -> None:
        super().__init__()
        self.keys = keys
        self.profile_url = self.WEB_URL + self.keys.public_key().to_bech32()

    @classmethod
    def from_metadata(cls, metadata: Metadata, keys: Keys) -> "AgentProfile":
        profile = cls(keys)
        profile.set_about(metadata.get_about())
        profile.set_display_name(metadata.get_display_name())
        profile.set_name(metadata.get_name())
        profile.set_picture(metadata.get_picture())
        profile.set_website(metadata.get_website())
        return profile

    def get_private_key(self) -> str:
        return str(self.keys.secret_key().to_bech32())

    def get_public_key(self) -> str:
        return str(self.keys.public_key().to_bech32())

    def to_json(self) -> str:
        # Parse parent's JSON string back to dict
        data = json.loads(super().to_json())
        # Add AgentProfile-specific fields
        data.update(
            {
                "profile_url": self.profile_url,
                "public_key": self.keys.public_key().to_bech32(),
                "private_key": self.keys.secret_key().to_bech32(),
            }
        )
        return json.dumps(data)


class MerchantProduct(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    stall_id: str
    name: str
    description: str
    images: List[str]
    currency: str
    price: float
    quantity: int
    shipping: List[ShippingCost]
    categories: Optional[List[str]] = []
    specs: Optional[List[List[str]]] = []

    @classmethod
    def from_product_data(cls, product_data: "ProductData") -> "MerchantProduct":
        # print(f"Raw product data specs: {product_data.specs}")  # Debug print
        shipping_costs = []
        for ship in product_data.shipping:
            if isinstance(ship, dict):
                shipping_costs.append(ShippingCost(id=ship["id"], cost=ship["cost"]))
            else:
                shipping_costs.append(ship)

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
            return ProductData(
                id=self.id,
                stall_id=self.stall_id,
                name=self.name,
                description=self.description,
                images=self.images,
                currency=self.currency,
                price=self.price,
                quantity=self.quantity,
                shipping=self.shipping,
                categories=self.categories,
                specs=self.specs,
            )
        except Exception as e:
            logging.error(f"Failed to convert to ProductData: {e}")
            logging.error(f"Shipping data: {self.shipping}")
            raise

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the MerchantProduct.
        ShippingCost class is not serializable, so we need to convert it to a dictionary.

        Returns:
            dict: dictionary representation of the MerchantProduct
        """
        shipping_dicts = []
        for shipping in self.shipping:
            shipping_dicts.append({"id": shipping.id, "cost": shipping.cost})

        return {
            "id": self.id,
            "stall_id": self.stall_id,
            "name": self.name,
            "description": self.description,
            "images": self.images,
            "currency": self.currency,
            "price": self.price,
            "quantity": self.quantity,
            "shipping": shipping_dicts,
            "categories": self.categories,
            "specs": self.specs,
        }


class MerchantStall(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    name: str
    description: str
    currency: str
    shipping: List[ShippingMethod]
    geohash: str

    @classmethod
    def from_stall_data(cls, stall: "StallData") -> "MerchantStall":
        return cls(
            id=stall.id(),
            name=stall.name(),
            description=stall.description(),
            currency=stall.currency(),
            shipping=stall.shipping(),
        )

    def get_geohash(self) -> str:
        return self.geohash

    def set_geohash(self, geohash: str) -> None:
        self.geohash = geohash

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the MerchantStall.
        ShippingMethod class is not serializable, so we need to convert it to a dictionary.
        We can only access cost and id from the ShippingMethod class. We can't access name or regions.

        Returns:
            dict: dictionary representation of the MerchantStall
        """
        shipping_dicts = []
        for shipping in self.shipping:
            shipping_dicts.append(
                {
                    "cost": shipping.get_shipping_cost().cost,
                    "id": shipping.get_shipping_cost().id,
                }
            )

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "currency": self.currency,
            "shipping zones": [shipping_dicts],
            "geohash": self.geohash,
        }

    def to_stall_data(self) -> "StallData":
        return StallData(
            self.id,
            self.name,
            self.description,
            self.currency,
            self.shipping,  # No conversion needed
        )
