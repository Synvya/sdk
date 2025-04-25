import json
import logging
import re
from enum import Enum
from typing import ClassVar, List, Optional, Set

import httpx
from nostr_sdk import (
    Alphabet,
    Event,
    JsonValue,
    Keys,
    Kind,
    Metadata,
    ProductData,
    PublicKey,
    ShippingCost,
    ShippingMethod,
    SingleLetterTag,
    StallData,
    TagKind,
)
from pydantic import BaseModel, ConfigDict, Field


class Namespace(str, Enum):
    """
    Represents a namespace.
    """

    MERCHANT = "com.synvya.merchant"
    GAMER = "com.synvya.gamer"
    OTHER = "com.synvya.other"

    """Configuration for Pydantic models to use enum values directly."""
    model_config = ConfigDict(use_enum_values=True)


class ProfileType(str, Enum):
    """
    Represents a profile type.
    """

    MERCHANT_RETAIL = "retail"
    MERCHANT_RESTAURANT = "restaurant"
    MERCHANT_SERVICE = "service"
    MERCHANT_BUSINESS = "business"
    MERCHANT_ENTERTAINMENT = "entertainment"
    MERCHANT_OTHER = "other"
    GAMER_DADJOKE = "dad-joke-game"
    OTHER_OTHER = "other"

    """Configuration for Pydantic models to use enum values directly."""
    model_config = ConfigDict(use_enum_values=True)


class ProfileFilter(BaseModel):
    """
    Represents a profile filter.
    """

    namespace: str
    profile_type: ProfileType
    hashtags: List[str]

    def __init__(
        self,
        namespace: str,
        profile_type: ProfileType,
        hashtags: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize a ProfileFilter instance.
        """
        normalized_hashtags = (
            [self._normalize_hashtag(tag) for tag in hashtags] if hashtags else []
        )
        super().__init__(
            namespace=namespace, profile_type=profile_type, hashtags=normalized_hashtags
        )
        self.namespace = namespace
        self.profile_type = profile_type
        self.hashtags = normalized_hashtags

    def to_json(self) -> str:
        """
        Convert the ProfileFilter to a JSON string.
        """
        return json.dumps(self.model_dump())

    @classmethod
    def from_json(cls, json_str: str) -> "ProfileFilter":
        """
        Create a ProfileFilter instance from a JSON string.
        """
        data = json.loads(json_str)
        return cls.model_validate(data)

    @staticmethod
    def _normalize_hashtag(tag: str) -> str:
        """
        Normalize hashtags by removing spaces, underscores, and hyphens,
        and converting to lowercase.
        Ensures consistent matching across variations.
        """
        tag = tag.lower()
        tag = re.sub(r"[\s\-_]+", "", tag)  # Remove spaces, hyphens, underscores
        return tag


class Profile(BaseModel):
    """
    Nostr Profile class.
    Contains public key only.
    """

    PROFILE_URL_PREFIX: ClassVar[str] = "https://primal.net/p/"
    logger: ClassVar[logging.Logger] = logging.getLogger("Profile")

    public_key: str
    about: str = ""
    banner: str = ""
    bot: bool = False
    display_name: str = ""
    hashtags: List[str] = []
    locations: Set[str] = Field(default_factory=set)
    name: str = ""
    namespace: str = ""
    nip05: str = ""
    nip05_validated: bool = False
    picture: str = ""
    profile_type: ProfileType = ProfileType.OTHER_OTHER
    profile_url: str = ""
    website: str = ""

    def __init__(self, public_key: str, **data) -> None:
        super().__init__(public_key=public_key, **data)
        self.profile_url = self.PROFILE_URL_PREFIX + public_key

    def add_hashtag(self, hashtag: str) -> None:
        normalized_hashtag = self._normalize_hashtag(hashtag)
        if normalized_hashtag not in self.hashtags:
            self.hashtags.append(normalized_hashtag)

    def add_location(self, location: str) -> None:
        self.locations.add(location)

    def get_about(self) -> str:
        return self.about

    def get_banner(self) -> str:
        return self.banner

    def get_display_name(self) -> str:
        return self.display_name

    def get_hashtags(self) -> List[str]:
        return self.hashtags

    def get_locations(self) -> set[str]:
        return self.locations

    def get_name(self) -> str:
        return self.name

    def get_namespace(self) -> str:
        return self.namespace

    def get_nip05(self) -> str:
        return self.nip05

    def get_picture(self) -> str:
        return self.picture

    def get_profile_type(self) -> ProfileType:
        return self.profile_type

    def get_profile_url(self) -> str:
        return self.profile_url

    def get_public_key(self, encoding: str = "bech32") -> str:
        """Get the public key of the Nostr profile.

        Args:
            encoding: encoding to use for the public key.
            Must be 'bech32' or 'hex'. Default is 'bech32'.

        Returns:
            str: public key of the Nostr profile in the specified encoding

        Raises:
            ValueError: if the encoding is not 'bech32' or 'hex'
        """
        if encoding == "bech32":
            return self.public_key
        if encoding == "hex":
            return PublicKey.parse(self.public_key).to_hex()

        raise ValueError("Invalid encoding. Must be 'bech32' or 'hex'.")

    def get_website(self) -> str:
        return self.website

    def is_bot(self) -> bool:
        return self.bot

    def is_nip05_validated(self) -> bool:
        return self.nip05_validated

    def matches_filter(self, profile_filter: ProfileFilter) -> bool:
        if self.namespace != profile_filter.namespace:
            return False
        if self.profile_type != profile_filter.type:
            return False
        if not all(hashtag in self.hashtags for hashtag in profile_filter.hashtags):
            return False
        return True

    def set_about(self, about: str) -> None:
        self.about = about

    def set_banner(self, banner: str) -> None:
        self.banner = self._validate_url(banner) if banner else ""

    def set_bot(self, bot: bool) -> None:
        self.bot = bot

    def set_display_name(self, display_name: str) -> None:
        self.display_name = display_name

    def set_name(self, name: str) -> None:
        self.name = name

    def set_namespace(self, namespace: Namespace | str) -> None:
        if isinstance(namespace, str):
            # Handle empty string by not setting any namespace
            if not namespace:
                self.namespace = ""
                return
            # Convert string to Namespace enum safely
            namespace = Namespace(namespace)
        self.namespace = namespace

    def set_nip05(self, nip05: str) -> None:
        self.nip05 = nip05

    def set_picture(self, picture: str) -> None:
        self.picture = self._validate_url(picture) if picture else ""

    def set_profile_type(self, profile_type: ProfileType | str) -> None:
        if isinstance(profile_type, str):
            # Convert string to ProfileType enum safely
            profile_type = ProfileType(profile_type)
        self.profile_type = profile_type

    def set_website(self, website: str) -> None:
        self.website = self._validate_url(website) if website else ""

    def to_dict(self) -> dict:
        return {
            "about": self.about,
            "banner": self.banner,
            "bot": self.bot,
            "display_name": self.display_name,
            "hashtags": self.hashtags,
            "locations": list(self.locations),  # Convert set to list
            "name": self.name,
            "namespace": self.namespace,
            "nip05": self.nip05,
            "picture": self.picture,
            "profile_url": self.profile_url,
            "public_key": self.public_key,
            "profile_type": self.profile_type,
            "website": self.website,
        }

    def to_json(self) -> str:
        data = {
            "about": self.about,
            "banner": self.banner,
            "bot": self.bot,
            "display_name": self.display_name,
            "hashtags": self.hashtags,
            "locations": (list(self.locations) if self.locations else []),
            "name": self.name,
            "namespace": self.namespace,
            "nip05": self.nip05,
            "picture": self.picture,
            "profile_url": self.profile_url,
            "public_key": self.public_key,
            "profile_type": self.profile_type.value,
            "website": self.website,
        }
        return json.dumps(data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Profile):
            return False
        return str(self.public_key) == str(other.public_key)

    def __hash__(self) -> int:
        return hash(str(self.public_key))

    async def _fetch_nip05_metadata(self, nip05: str) -> dict:
        """
        Fetch NIP-05 metadata from the well-known URL.

        Args:
            nip05: NIP-05 identifier in the format username@domain

        Returns:
            dict: Parsed JSON response containing metadata

        Raises:
            RuntimeError: if the request fails or returns an error
        """
        if "@" not in nip05:
            raise ValueError("Invalid NIP-05 format. Expected name@domain.")

        name, domain = nip05.split("@")
        url = f"https://{domain}/.well-known/nostr.json?name={name}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()  # Raise an error for bad responses
                return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Failed to fetch NIP-05 metadata for {nip05}: {e.response.text}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while fetching NIP-05 metadata: {e}"
            ) from e

    async def _validate_profile_nip05(self) -> bool:
        if not self.nip05:
            self.logger.error("Profile has no NIP-05")
            return False
        if self.nip05.startswith("@"):
            self.logger.error("Profile NIP-05 must not start with @")
            return False

        try:
            # Extract the local part (username) from the NIP-05 identifier
            local_part = self.nip05.split("@")[0]
            nostr_json = await self._fetch_nip05_metadata(self.nip05)
        except Exception as e:
            self.logger.error("Failed to fetch NIP-05 metadata: %s", e)
            return False

        if "names" in nostr_json:
            for name, public_key in nostr_json["names"].items():
                if (
                    name.lower() == local_part.lower()
                    and public_key == self.get_public_key("hex")
                ):
                    return True
        else:
            return False

    def _validate_url(self, url: str) -> str:
        if not url:
            return ""
        if not url.startswith(("http://", "https://")):
            return ""
        return url

    @classmethod
    async def from_metadata(cls, metadata: Metadata, public_key: str) -> "Profile":
        """
        Create a Profile instance from a Metadata object.
        TBD: Add logic to set namespace, type and hashtags from Metadata.
        """
        profile = cls(public_key)
        profile.set_about(metadata.get_about())
        profile.set_banner(metadata.get_banner())
        profile.set_display_name(metadata.get_display_name())
        profile.set_name(metadata.get_name())
        profile.set_nip05(metadata.get_nip05())
        profile.set_picture(metadata.get_picture())
        profile.set_website(metadata.get_website())
        json_bot = metadata.get_custom_field("bot")
        if isinstance(json_bot, JsonValue.BOOL):
            profile.set_bot(json_bot.bool)
        else:
            profile.set_bot(False)
        try:
            profile.nip05_validated = await profile._validate_profile_nip05()

        except Exception as e:
            profile.logger.error("Failed to validate NIP-05: %s", e)
            profile.nip05_validated = False
        return profile

    @classmethod
    async def from_event(cls, event: Event) -> "Profile":
        """
        Create a Profile instance from a kind:0 Nostr event.

        Args:
            event: kind:0 Nostr event

        Returns:
            Profile: Profile instance

        Raises:
            ValueError: if the event is not a kind:0 Nostr event
        """

        if event.kind() != Kind(0):
            raise ValueError("Event is not a kind:0 Nostr event")

        profile = cls(event.author().to_bech32())

        # Process metadata
        metadata = json.loads(event.content())
        profile.set_about(metadata.get("about", ""))
        profile.set_banner(metadata.get("banner", ""))
        profile.set_bot(metadata.get("bot", False))
        profile.set_display_name(metadata.get("display_name", ""))
        profile.set_name(metadata.get("name", ""))
        profile.set_nip05(metadata.get("nip05", ""))
        profile.set_picture(metadata.get("picture", ""))
        profile.set_website(metadata.get("website", ""))

        # process tags
        tags = event.tags()
        hashtag_list = tags.hashtags()
        for hashtag in hashtag_list:
            profile.add_hashtag(hashtag)

        namespace_tag = tags.find(
            TagKind.SINGLE_LETTER(SingleLetterTag.uppercase(Alphabet.L))
        )
        if namespace_tag is not None:
            profile.set_namespace(namespace_tag.content())

        profile_type_tag = tags.find(
            TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L))
        )
        if profile_type_tag is not None:
            profile.set_profile_type(profile_type_tag.content())

        try:
            profile.nip05_validated = await profile._validate_profile_nip05()
        except Exception as e:
            profile.logger.error("Failed to validate NIP-05: %s", e)
            profile.nip05_validated = False
        return profile

    @classmethod
    def from_json(cls, json_str: str) -> "Profile":
        """
        Create a Profile instance from a JSON string.

        Args:
            json_str (str): JSON string containing profile information.

        Returns:
            Profile: An instance of Profile.
        """
        data = json.loads(json_str)
        profile = cls(public_key=data["public_key"])
        profile.set_about(data.get("about", ""))
        profile.set_banner(data.get("banner", ""))
        profile.set_bot(data.get("bot", False))
        profile.set_display_name(data.get("display_name", ""))
        for hashtag in data.get("hashtags", []):
            profile.add_hashtag(hashtag)
        profile.set_namespace(data.get("namespace", ""))
        profile.set_name(data.get("name", ""))
        profile.set_nip05(data.get("nip05", ""))
        profile.set_picture(data.get("picture", ""))
        profile.set_profile_type(data.get("profile_type", ProfileType.OTHER_OTHER))
        profile.set_website(data.get("website", ""))
        profile.locations = set(data.get("locations", []))
        return profile

    @staticmethod
    def _normalize_hashtag(tag: str) -> str:
        """
        Normalize hashtags by removing spaces, underscores, and hyphens,
        and converting to lowercase.
        Ensures consistent matching across variations.
        """
        tag = tag.lower()
        tag = re.sub(r"[\s\-_]+", "", tag)  # Remove spaces, hyphens, underscores
        return tag


class NostrKeys(BaseModel):
    """
    NostrKeys is a class that contains a public and private key
    in bech32 format.
    """

    public_key: str
    private_key: str

    def __init__(self, public_key: str, private_key: str) -> None:
        """
        Initialize a NostrKeys instance.
        """
        super().__init__(public_key=public_key, private_key=private_key)
        self.public_key = public_key
        self.private_key = private_key

    def get_public_key(self, encoding: str = "bech32") -> str:
        """
        Get the public key.

        Args:
            encoding (str, optional): The encoding format for the public key.
            Must be 'bech32' or 'hex'. Default is 'bech32'.

        Returns:
            str: public key

        Raises:
            ValueError: If the encoding is not 'bech32' or 'hex'.
        """
        if encoding == "bech32":
            return self.public_key
        elif encoding == "hex":
            return PublicKey.parse(self.public_key).to_hex()
        else:
            raise ValueError("Invalid encoding. Must be 'bech32' or 'hex'.")

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
    def derive_public_key(cls, private_key: str, encoding: str = "bech32") -> str:
        """
        Class method to parse a private key and return a public key
        in bech32 or hex format.

        Args:
            private_key (str): The private key to derive the public key from.
            encoding (str): The encoding to use for the public key. Must be
            'bech32' or 'hex'. Default is 'bech32'.

        Returns:
            str: The public key in the specified encoding.

        Raises:
            ValueError: If the encoding is not 'bech32' or 'hex'.
        """
        if encoding not in {"bech32", "hex"}:
            raise ValueError("Invalid format. Must be 'bech32' or 'hex'.")
        if encoding == "bech32":
            return Keys.parse(private_key).public_key().to_bech32()
        if encoding == "hex":
            return Keys.parse(private_key).public_key().to_hex()


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
    ssm_regions: List[str] = Field(default_factory=list)

    def __init__(
        self,
        ssm_id: str,
        ssm_cost: float,
        ssm_name: str,
        ssm_regions: Optional[List[str]] = None,
    ) -> None:
        super().__init__(
            ssm_id=ssm_id,
            ssm_cost=ssm_cost,
            ssm_name=ssm_name,
            ssm_regions=ssm_regions if ssm_regions is not None else [],
        )
        self.ssm_id = ssm_id
        self.ssm_cost = ssm_cost
        self.ssm_name = ssm_name
        self.ssm_regions = ssm_regions if ssm_regions is not None else []

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
        return (
            f"ID: {self.ssm_id} "
            f"Cost: {self.ssm_cost} "
            f"Name: {self.ssm_name} "
            f"Regions: {self.ssm_regions}"
        )


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
    seller: str

    def set_seller(self, seller: str) -> None:
        """
        Set the seller of the product.
        Use it to set the seller after creating a Product using the
        @classmethod from_product_data() since ProductData does not contain
        the seller's public key.

        Args:
            seller: str in bech32 format
        """
        self.seller = seller

    def get_seller(self) -> str:
        """Get the seller of the product.

        Returns:
            str: seller of the product in bech32 format
        """
        return self.seller

    @classmethod
    def from_product_data(cls, product_data: "ProductData") -> "Product":
        shipping_costs = []
        for ship in product_data.shipping:
            if isinstance(ship, dict):
                shipping_costs.append(
                    ProductShippingCost(psc_id=ship["id"], psc_cost=ship["cost"])
                )
            else:
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
            seller="",
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
            "seller": self.seller,
        }

    def to_json(self) -> str:
        """
        Returns a JSON string representation of the Product.

        Returns:
            str: JSON string representation of the Product
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Product":
        """
        Create a Product instance from a JSON string.

        Args:
            json_str (str): JSON string containing product information.

        Returns:
            Product: An instance of Product.
        """
        data = json.loads(json_str)
        shipping_costs = [
            ProductShippingCost(psc_id=ship["id"], psc_cost=ship["cost"])
            for ship in data.get("shipping", [])
        ]
        return cls(
            id=data["id"],
            stall_id=data["stall_id"],
            name=data["name"],
            description=data["description"],
            images=data.get("images", []),
            currency=data["currency"],
            price=data["price"],
            quantity=data["quantity"],
            shipping=shipping_costs,
            categories=data.get("categories", []),
            specs=data.get("specs", []),
            seller=data["seller"],
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return False
        return str(self.id) == str(other.id)


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

    def get_geohash(self) -> str:
        return self.geohash

    def set_geohash(self, geohash: str) -> None:
        self.geohash = geohash

    def to_dict(self) -> dict:
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

    def to_json(self) -> str:
        """
        Returns a JSON string representation of the Stall.

        Returns:
            str: JSON string representation of the Stall
        """
        return json.dumps(self.to_dict())

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
        # Handle empty strings
        if not stall_content or stall_content.isspace():
            return cls(
                id="unknown",
                name="Unknown Stall",
                description="",
                currency="USD",
                shipping=[],
            )

        # Parse the JSON string into a data structure
        try:
            data = json.loads(stall_content)
        except json.JSONDecodeError:
            # Return default stall if JSON parsing fails
            return cls(
                id="unknown",
                name="Unknown Stall",
                description="",
                currency="USD",
                shipping=[],
            )

        # If data is an empty list, create a default Stall
        if isinstance(data, list):
            if not data:  # Empty list
                return cls(
                    id="unknown",
                    name="Unknown Stall",
                    description="",
                    currency="USD",
                    shipping=[],
                )
            # If it's a non-empty list, use the first item
            data = data[0] if isinstance(data[0], dict) else {}

        # Ensure data is a dictionary at this point
        if not isinstance(data, dict):
            # If data is neither a list nor a dict, create a default stall
            return cls(
                id="unknown",
                name="Unknown Stall",
                description="",
                currency="USD",
                shipping=[],
            )

        # Create a list of StallShippingMethod from the shipping data
        shipping_methods = []
        # Handle stalls that might not have shipping data
        if "shipping" in data:
            for shipping in data.get("shipping", []):
                if not isinstance(shipping, dict):
                    continue
                # Handle case where regions might be None
                regions = shipping.get("regions", [])
                try:
                    shipping_methods.append(
                        StallShippingMethod(
                            ssm_id=shipping.get("id", "unknown"),
                            ssm_cost=float(shipping.get("cost", 0.0)),
                            ssm_name=shipping.get("name", ""),
                            ssm_regions=regions if regions is not None else [],
                        )
                    )
                except (ValueError, TypeError):
                    # Skip this shipping method if any errors occur
                    continue

        # Handle missing required fields with defaults
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", data.get("title", "")),  # Try title as fallback
            description=data.get("description", ""),
            currency=data.get("currency", "USD"),  # Default to USD
            shipping=shipping_methods,
            geohash=data.get("geohash", None),
        )
