import json
import logging
import re
import warnings
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import ClassVar, Dict, List, Literal, Optional, Set

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
    Tag,
    TagKind,
)
from pydantic import BaseModel, ConfigDict, Field


def deprecated(reason: str, version: str = "2.0.0", alternative: str = None):
    """
    Decorator to mark functions as deprecated.

    Args:
        reason: Why the function is deprecated
        version: Version when it will be removed
        alternative: Suggested alternative function/method
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            message = f"{func.__name__} is deprecated. {reason}"
            if alternative:
                message += f" Use {alternative} instead."
            message += f" Will be removed in version {version}."

            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        # Update docstring
        if func.__doc__:
            func.__doc__ += f"\n\n.. deprecated:: {version}\n    {reason}"
            if alternative:
                func.__doc__ += f" Use :func:`{alternative}` instead."

        return wrapper

    return decorator


class KeyEncoding(str, Enum):
    """
    Enum representing the valid encoding formats for public or private keys.

    Attributes:
        BECH32 (str): Encodes the key using Bech32 format.
        HEX (str): Encodes the key using hexadecimal format.
    """

    BECH32 = "bech32"
    HEX = "hex"

    @classmethod
    def from_str(cls, value: str) -> "KeyEncoding":
        """
        Convert a string to a KeyEncoding enum value, case-insensitively.

        Args:
            value (str): The input string, e.g. "bech32" or "HEX".

        Returns:
            KeyEncoding: A corresponding enum value.

        Raises:
            ValueError: If the input is not a valid encoding.
        """
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(
                f"Invalid encoding: '{value}'. Must be one of: {[e.value for e in cls]}"
            )


class Namespace(str, Enum):
    """
    Represents a namespace.
    """

    MERCHANT = "com.synvya.merchant"
    GAMER = "com.synvya.gamer"
    OTHER = "com.synvya.other"
    BUSINESS_TYPE = "business.type"

    """Configuration for Pydantic models to use enum values directly."""
    model_config = ConfigDict(use_enum_values=True)


class ProfileType(str, Enum):
    """
    Represents a profile type.
    """

    RETAIL = "retail"
    RESTAURANT = "restaurant"
    SERVICE = "service"
    BUSINESS = "business"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"
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
        Normalize hashtags by converting to lowercase.
        Ensures consistent matching across variations.
        """
        tag = tag.lower()
        # tag = re.sub(r"[\s\-_]+", "", tag)  # Remove spaces, hyphens, underscores
        return tag


class Profile(BaseModel):
    """
    Nostr Profile class.
    Contains public key only.
    """

    PROFILE_URL_PREFIX: ClassVar[str] = "https://primal.net/p/"
    logger: ClassVar[logging.Logger] = logging.getLogger("Profile")

    public_key: str  # stored in hex format
    about: str = ""
    banner: str = ""
    bot: bool = False
    city: str = ""
    country: str = ""
    created_at: int = 0
    display_name: str = ""
    email: str = ""
    hashtags: List[str] = []
    locations: Set[str] = Field(default_factory=set)
    name: str = ""
    namespace: str = ""
    nip05: str = ""
    nip05_validated: bool = False
    picture: str = ""
    phone: str = ""
    profile_type: ProfileType = ProfileType.OTHER_OTHER
    profile_url: str = ""
    state: str = ""
    street: str = ""
    website: str = ""
    zip_code: str = ""
    environment: Literal["production", "demo"] = "production"

    def __init__(self, public_key: str, **data) -> None:
        """
        Initialize a Profile instance.
        Args:
            public_key: Public key of the Nostr profile in hex or bech32 format.
            **data: Additional data to initialize the Profile instance.

        Returns:
            None
        """
        public_key = PublicKey.parse(public_key).to_hex()
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

    def get_city(self) -> str:
        return self.city

    def get_country(self) -> str:
        return self.country

    def get_created_at(self) -> int:
        return self.created_at

    def get_display_name(self) -> str:
        return self.display_name

    def get_environment(self) -> Literal["production", "demo"]:
        return self.environment

    def get_email(self) -> str:
        return self.email

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

    def get_phone(self) -> str:
        return self.phone

    def get_picture(self) -> str:
        return self.picture

    def get_profile_type(self) -> ProfileType:
        return self.profile_type

    def get_profile_url(self) -> str:
        return self.profile_url

    def get_public_key(self, encoding: KeyEncoding = KeyEncoding.BECH32) -> str:
        """Get the public key of the Nostr profile.

        Args:
            encoding: encoding to use for the public key.
            Must be 'bech32' or 'hex'. Default is 'bech32'.

        Returns:
            str: public key of the Nostr profile in the specified encoding

        Raises:
            ValueError: if the encoding is not 'bech32' or 'hex'
        """
        if encoding == KeyEncoding.BECH32:
            return PublicKey.parse(self.public_key).to_bech32()
        if encoding == KeyEncoding.HEX:
            return PublicKey.parse(self.public_key).to_hex()

        raise ValueError("Invalid encoding. Must be 'bech32' or 'hex'.")

    def get_state(self) -> str:
        return self.state

    def get_street(self) -> str:
        return self.street

    def get_website(self) -> str:
        return self.website

    def get_zip_code(self) -> str:
        return self.zip_code

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

    def set_city(self, city: str) -> None:
        self.city = city

    def set_country(self, country: str) -> None:
        self.country = country

    def set_created_at(self, created_at: int) -> None:
        self.created_at = created_at

    def set_display_name(self, display_name: str) -> None:
        self.display_name = display_name

    def set_environment(self, environment: Literal["production", "demo"]) -> None:
        self.environment = environment

    def set_email(self, email: str) -> None:
        self.email = email

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

    def set_phone(self, phone: str) -> None:
        self.phone = phone

    def set_profile_type(self, profile_type: ProfileType | str) -> None:
        if isinstance(profile_type, str):
            # Convert string to ProfileType enum safely
            profile_type = ProfileType(profile_type)
        self.profile_type = profile_type

    def set_state(self, state: str) -> None:
        self.state = state

    def set_street(self, street: str) -> None:
        self.street = street

    def set_website(self, website: str) -> None:
        self.website = self._validate_url(website) if website else ""

    def set_zip_code(self, zip_code: str) -> None:
        self.zip_code = zip_code

    def to_dict(self) -> dict:
        return {
            "about": self.about,
            "banner": self.banner,
            "bot": self.bot,
            "city": self.city,
            "country": self.country,
            "created_at": self.created_at,
            "display_name": self.display_name,
            "environment": self.environment,
            "email": self.email,
            "hashtags": self.hashtags,
            "locations": list(self.locations),  # Convert set to list
            "name": self.name,
            "namespace": self.namespace,
            "nip05": self.nip05,
            "picture": self.picture,
            "phone": self.phone,
            "profile_url": self.profile_url,
            "public_key": self.public_key,
            "profile_type": self.profile_type,
            "state": self.state,
            "street": self.street,
            "website": self.website,
            "zip_code": self.zip_code,
        }

    def to_json(self) -> str:
        data = {
            "about": self.about,
            "banner": self.banner,
            "bot": self.bot,
            "city": self.city,
            "country": self.country,
            "created_at": self.created_at,
            "display_name": self.display_name,
            "environment": self.environment,
            "email": self.email,
            "hashtags": self.hashtags,
            "locations": (list(self.locations) if self.locations else []),
            "name": self.name,
            "namespace": self.namespace,
            "nip05": self.nip05,
            "picture": self.picture,
            "phone": self.phone,
            "profile_url": self.profile_url,
            "public_key": self.public_key,
            "profile_type": self.profile_type.value,
            "state": self.state,
            "street": self.street,
            "website": self.website,
            "zip_code": self.zip_code,
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
    @deprecated(
        reason="Method is incomplete and lacks namespace/type/hashtags logic",
        alternative="from_event",
    )
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

        json_environment = metadata.get_custom_field("environment")
        if isinstance(json_environment, JsonValue.STR):
            profile.set_environment(json_environment.s)
        else:
            profile.set_environment("production")

        # json_city = metadata.get_custom_field("city")
        # if isinstance(json_city, JsonValue.STR):
        #     profile.set_city(json_city.s)
        # else:
        #     profile.set_city("")

        # json_country = metadata.get_custom_field("country")
        # if isinstance(json_country, JsonValue.STR):
        #     profile.set_country(json_country.s)
        # else:
        #     profile.set_country("")

        # json_email = metadata.get_custom_field("email")
        # if isinstance(json_email, JsonValue.STR):
        #     profile.set_email(json_email.s)
        # else:
        #     profile.set_email("")

        # json_phone = metadata.get_custom_field("phone")
        # if isinstance(json_phone, JsonValue.STR):
        #     profile.set_phone(json_phone.s)
        # else:
        #     profile.set_phone("")

        # json_state = metadata.get_custom_field("state")
        # if isinstance(json_state, JsonValue.STR):
        #     profile.set_state(json_state.s)
        # else:
        #     profile.set_state("")

        # json_street = metadata.get_custom_field("street")
        # if isinstance(json_street, JsonValue.STR):
        #     profile.set_street(json_street.s)
        # else:
        #     profile.set_street("")

        # json_zip_code = metadata.get_custom_field("zip_code")
        # if isinstance(json_zip_code, JsonValue.STR):
        #     profile.set_zip_code(json_zip_code.s)
        # else:
        #     profile.set_zip_code("")

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

        profile = cls(event.author().to_hex())

        # Process metadata
        metadata = json.loads(event.content())
        profile.set_about(metadata.get("about", ""))
        profile.set_banner(metadata.get("banner", ""))
        profile.set_bot(metadata.get("bot", False))
        # profile.set_city(metadata.get("city", ""))
        # profile.set_country(metadata.get("country", ""))
        profile.set_display_name(metadata.get("display_name", ""))
        profile.set_environment(metadata.get("environment", "production"))
        # profile.set_email(metadata.get("email", ""))
        profile.set_name(metadata.get("name", ""))
        profile.set_nip05(metadata.get("nip05", ""))
        profile.set_picture(metadata.get("picture", ""))
        # profile.set_phone(metadata.get("phone", ""))
        # profile.set_state(metadata.get("state", ""))
        # profile.set_street(metadata.get("street", ""))
        profile.set_website(metadata.get("website", ""))
        # profile.set_zip_code(metadata.get("zip_code", ""))

        profile.set_created_at(event.created_at().as_secs())

        # process tags
        tags = event.tags()

        tag_vector: List[Tag] = tags.to_vec()

        for tag in tag_vector:
            if tag.kind() == TagKind.SINGLE_LETTER(
                SingleLetterTag.lowercase(Alphabet.I)
            ):
                # Extract identity claims from i-tags
                tag_content = tag.content()
                if ":" in tag_content:
                    claim_type, identity = tag_content.split(":", 1)

                    if claim_type == "email":
                        profile.set_email(identity)
                    elif claim_type == "phone":
                        profile.set_phone(identity)
                    elif claim_type == "location":
                        # Parse location string into components
                        # Expected format: street, city, state, country, zip_code
                        # Modify expected format to: street, city, state, zip_code, country
                        location_parts = [part.strip() for part in identity.split(",")]

                        if len(location_parts) >= 1:
                            profile.set_street(location_parts[0])
                        if len(location_parts) >= 2:
                            profile.set_city(location_parts[1])
                        if len(location_parts) >= 3:
                            profile.set_state(location_parts[2])
                        if len(location_parts) >= 4:
                            profile.set_zip_code(location_parts[3])
                        if len(location_parts) >= 5:
                            profile.set_country(location_parts[4])

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
        profile.logger.debug("Profile: %s", profile)
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
        profile.set_city(data.get("city", ""))
        profile.set_country(data.get("country", ""))
        profile.set_created_at(data.get("created_at", 0))
        profile.set_display_name(data.get("display_name", ""))
        profile.set_environment(data.get("environment", "production"))
        profile.set_email(data.get("email", ""))
        for hashtag in data.get("hashtags", []):
            profile.add_hashtag(hashtag)
        profile.locations = set(data.get("locations", []))
        profile.set_namespace(data.get("namespace", ""))
        profile.set_name(data.get("name", ""))
        profile.set_nip05(data.get("nip05", ""))
        profile.set_picture(data.get("picture", ""))
        profile.set_phone(data.get("phone", ""))
        profile.set_profile_type(data.get("profile_type", ProfileType.OTHER_OTHER))
        profile.set_state(data.get("state", ""))
        profile.set_street(data.get("street", ""))
        profile.set_website(data.get("website", ""))
        profile.set_zip_code(data.get("zip_code", ""))

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
    NostrKeys is a class that contains a public and private key.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    keys: Keys

    def __init__(self, private_key: Optional[str] = None) -> None:
        """
        Initialize a NostrKeys instance.
        If no private key is provided, a new one will be generated.
        Args:
            private_key: str in bech32 or hex format
        """
        if private_key is None:
            keys = Keys.generate()
        else:
            keys = Keys.parse(private_key)

        super().__init__(keys=keys)

    def get_public_key(self, encoding: KeyEncoding = KeyEncoding.BECH32) -> str:
        """
        Get the public key.

        Args:
            encoding (KeyEncoding, optional): The encoding format for the public key.

        Returns:
            str: public key

        Raises:
            ValueError: If the encoding is not 'bech32' or 'hex'.
        """
        if isinstance(encoding, str):
            try:
                encoding = KeyEncoding(encoding.lower())
            except ValueError as e:
                raise ValueError(
                    f"Invalid encoding. Must be one of: {[e.value for e in KeyEncoding]}"
                ) from e

        match encoding:
            case KeyEncoding.BECH32:
                return self.keys.public_key().to_bech32()
            case KeyEncoding.HEX:
                return self.keys.public_key().to_hex()

    def get_private_key(self, encoding: KeyEncoding = KeyEncoding.BECH32) -> str:
        """
        Get the private key.

        Args:
            encoding (KeyEncoding, optional): The encoding format for the public key.

        Returns:
            str: private key

        Raises:
            ValueError: If the encoding is not 'bech32' or 'hex'.
        """
        if isinstance(encoding, str):
            try:
                encoding = KeyEncoding(encoding.lower())
            except ValueError as e:
                raise ValueError(
                    f"Invalid encoding. Must be one of: {[e.value for e in KeyEncoding]}"
                ) from e

        match encoding:
            case KeyEncoding.BECH32:
                return self.keys.secret_key().to_bech32()
            case KeyEncoding.HEX:
                return self.keys.secret_key().to_hex()

    def to_json(self, encoding: KeyEncoding = KeyEncoding.BECH32) -> str:
        """
        Returns a JSON representation of the NostrKeys object.

        The resulting JSON contains both the public and private keys in bech32 format.

        Returns:
            str: JSON string with keys.
        """
        if isinstance(encoding, str):
            try:
                encoding = KeyEncoding(encoding.lower())
            except ValueError as e:
                raise ValueError(
                    f"Invalid encoding. Must be one of: {[e.value for e in KeyEncoding]}"
                ) from e

        match encoding:
            case KeyEncoding.BECH32:
                return json.dumps(
                    {
                        "public_key": self.keys.public_key().to_bech32(),
                        "private_key": self.keys.secret_key().to_bech32(),
                    }
                )
            case KeyEncoding.HEX:
                return json.dumps(
                    {
                        "public_key": self.keys.public_key().to_hex(),
                        "private_key": self.keys.secret_key().to_hex(),
                    }
                )

    def __str__(self) -> str:
        """Return a string representation of the NostrKeys object using bech32 encoding."""
        return f"Public_key: {self.keys.public_key().to_bech32()} \nPrivate_key: {self.keys.secret_key().to_bech32()}"

    @classmethod
    @deprecated(
        reason="Use new NostrKeys constructor instead.",
        alternative="NostrKeys(private_key=private_key)",
    )
    def from_private_key(cls, private_key: str) -> "NostrKeys":
        """Create a NostrKeys object from a private key."""
        return cls(private_key)

    @classmethod
    def derive_public_key(
        cls, private_key: str, encoding: KeyEncoding = KeyEncoding.BECH32
    ) -> str:
        """
        Class method to parse a private key and return a public key
        in bech32 or hex format.

        Args:
            private_key (str): The private key to derive the public key from.
            encoding (KeyEncoding): The encoding to use for the public key.

        Returns:
            str: The public key in the specified encoding.

        Raises:
            ValueError: If the encoding is not 'bech32' or 'hex'.
        """
        if isinstance(encoding, str):
            try:
                encoding = KeyEncoding(encoding.lower())
            except ValueError as e:
                raise ValueError(
                    f"Invalid encoding. Must be one of: {[e.value for e in KeyEncoding]}"
                ) from e
        match encoding:
            case KeyEncoding.BECH32:
                return Keys.parse(private_key).public_key().to_bech32()
            case KeyEncoding.HEX:
                return Keys.parse(private_key).public_key().to_hex()


def _extract_nostr_tags(event: "Event") -> List[List[str]]:
    """
    Extract the raw tag arrays from a nostr_sdk Event.
    """
    tags_data: List[List[str]] = []

    as_json = getattr(event, "as_json", None)
    if callable(as_json):
        try:
            raw_event = as_json()
            event_dict = (
                json.loads(raw_event) if isinstance(raw_event, str) else raw_event
            )
            raw_tags = event_dict.get("tags", [])
            for tag in raw_tags:
                if isinstance(tag, list):
                    tags_data.append([str(item) for item in tag])
            if tags_data:
                return tags_data
        except Exception:
            tags_data = []

    try:
        tags_obj = event.tags()
        to_vec = getattr(tags_obj, "to_vec", None)
        if callable(to_vec):
            for tag in to_vec():
                tag_values = None
                as_vec = getattr(tag, "as_vec", None)
                if callable(as_vec):
                    tag_values = as_vec()
                elif hasattr(tag, "as_json"):
                    try:
                        maybe_json = tag.as_json()
                        tag_values = (
                            json.loads(maybe_json)
                            if isinstance(maybe_json, str)
                            else maybe_json
                        )
                    except Exception:
                        tag_values = None
                if not tag_values or not isinstance(tag_values, list):
                    continue
                tags_data.append([str(item) for item in tag_values])
    except Exception:
        return tags_data

    return tags_data


class ClassifiedListing(BaseModel):
    """
    Represents a marketplace classified listing (kind 30402).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    title: str
    description: str = ""
    price_amount: Optional[float] = None
    price_currency: Optional[str] = None
    price_frequency: Optional[str] = None
    listing_type: str = "simple"
    listing_format: str = "digital"
    visibility: str = "on-sale"
    stock: Optional[int] = None
    summary: Optional[str] = None
    images: List[Dict[str, Optional[str]]] = Field(default_factory=list)
    specs: List[List[str]] = Field(default_factory=list)
    weight_value: Optional[str] = None
    weight_unit: Optional[str] = None
    dimensions_value: Optional[str] = None
    dimensions_unit: Optional[str] = None
    location: Optional[str] = None
    geohash: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    shipping_options: List[Dict[str, Optional[str]]] = Field(default_factory=list)
    collections: List[str] = Field(default_factory=list)
    seller: str = ""

    def set_seller(self, seller: str) -> None:
        self.seller = seller

    def get_seller(self) -> str:
        return self.seller

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": {
                "amount": self.price_amount,
                "currency": self.price_currency,
                "frequency": self.price_frequency,
            },
            "listing_type": self.listing_type,
            "listing_format": self.listing_format,
            "visibility": self.visibility,
            "stock": self.stock,
            "summary": self.summary,
            "images": self.images,
            "specs": self.specs,
            "weight": {"value": self.weight_value, "unit": self.weight_unit},
            "dimensions": {
                "value": self.dimensions_value,
                "unit": self.dimensions_unit,
            },
            "location": self.location,
            "geohash": self.geohash,
            "categories": self.categories,
            "shipping_options": self.shipping_options,
            "collections": self.collections,
            "seller": self.seller,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_event(cls, event: "Event") -> "ClassifiedListing":
        tags_data = _extract_nostr_tags(event)

        def find_first(name: str) -> Optional[List[str]]:
            for tag in tags_data:
                if tag and tag[0] == name:
                    return tag
            return None

        def find_all(name: str) -> List[List[str]]:
            return [tag for tag in tags_data if tag and tag[0] == name]

        id_tag = find_first("d")
        title_tag = find_first("title")
        price_tag = find_first("price")
        type_tag = find_first("type")
        visibility_tag = find_first("visibility")
        stock_tag = find_first("stock")
        summary_tag = find_first("summary")
        weight_tag = find_first("weight")
        dim_tag = find_first("dim")
        location_tag = find_first("location")
        geohash_tag = find_first("g")

        identifier = id_tag[1] if id_tag and len(id_tag) > 1 else ""
        title = title_tag[1] if title_tag and len(title_tag) > 1 else ""

        price_amount: Optional[float] = None
        price_currency: Optional[str] = None
        price_frequency: Optional[str] = None
        if price_tag and len(price_tag) > 2:
            try:
                price_amount = float(price_tag[1])
            except (TypeError, ValueError):
                price_amount = None
            price_currency = price_tag[2]
            if len(price_tag) > 3:
                price_frequency = price_tag[3]

        listing_type = type_tag[1] if type_tag and len(type_tag) > 1 else "simple"
        listing_format = type_tag[2] if type_tag and len(type_tag) > 2 else "digital"
        visibility = (
            visibility_tag[1]
            if visibility_tag and len(visibility_tag) > 1
            else "on-sale"
        )

        stock: Optional[int] = None
        if stock_tag and len(stock_tag) > 1:
            try:
                stock = int(stock_tag[1])
            except (TypeError, ValueError):
                stock = None

        summary = summary_tag[1] if summary_tag and len(summary_tag) > 1 else None
        weight_value = weight_tag[1] if weight_tag and len(weight_tag) > 1 else None
        weight_unit = weight_tag[2] if weight_tag and len(weight_tag) > 2 else None
        dimensions_value = dim_tag[1] if dim_tag and len(dim_tag) > 1 else None
        dimensions_unit = dim_tag[2] if dim_tag and len(dim_tag) > 2 else None
        location = location_tag[1] if location_tag and len(location_tag) > 1 else None
        geohash = geohash_tag[1] if geohash_tag and len(geohash_tag) > 1 else None

        images: List[Dict[str, Optional[str]]] = []
        for image_tag in find_all("image"):
            image_entry: Dict[str, Optional[str]] = {}
            if len(image_tag) > 1:
                image_entry["url"] = image_tag[1]
            if len(image_tag) > 2:
                image_entry["dimensions"] = image_tag[2]
            if len(image_tag) > 3:
                image_entry["order"] = image_tag[3]
            images.append(image_entry)

        specs = [
            [spec_tag[1], spec_tag[2]]
            for spec_tag in find_all("spec")
            if len(spec_tag) > 2
        ]

        categories = [cat_tag[1] for cat_tag in find_all("t") if len(cat_tag) > 1]

        shipping_options = []
        for opt_tag in find_all("shipping_option"):
            entry: Dict[str, Optional[str]] = {}
            if len(opt_tag) > 1:
                entry["reference"] = opt_tag[1]
            if len(opt_tag) > 2:
                entry["extra_cost"] = opt_tag[2]
            shipping_options.append(entry)

        collections = [
            col_tag[1]
            for col_tag in find_all("a")
            if len(col_tag) > 1 and col_tag[1].startswith("30405:")
        ]

        try:
            seller = event.author().to_bech32()
        except Exception:
            seller = event.author().to_hex()

        return cls(
            id=identifier,
            title=title,
            description=event.content() or "",
            price_amount=price_amount,
            price_currency=price_currency,
            price_frequency=price_frequency,
            listing_type=listing_type,
            listing_format=listing_format,
            visibility=visibility,
            stock=stock,
            summary=summary,
            images=images,
            specs=specs,
            weight_value=weight_value,
            weight_unit=weight_unit,
            dimensions_value=dimensions_value,
            dimensions_unit=dimensions_unit,
            location=location,
            geohash=geohash,
            categories=categories,
            shipping_options=shipping_options,
            collections=collections,
            seller=seller,
        )


class Collection(BaseModel):
    """
    Represents a product collection (kind 30405).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    title: str
    description: str = ""
    product_references: List[str] = Field(default_factory=list)
    image: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    geohash: Optional[str] = None
    shipping_options: List[Dict[str, Optional[str]]] = Field(default_factory=list)
    author: str = ""

    def set_author(self, author: str) -> None:
        self.author = author

    def get_author(self) -> str:
        return self.author

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "product_references": self.product_references,
            "image": self.image,
            "summary": self.summary,
            "location": self.location,
            "geohash": self.geohash,
            "shipping_options": self.shipping_options,
            "author": self.author,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_event(cls, event: "Event") -> "Collection":
        tags_data = _extract_nostr_tags(event)

        def find_first(name: str) -> Optional[List[str]]:
            for tag in tags_data:
                if tag and tag[0] == name:
                    return tag
            return None

        def find_all(name: str) -> List[List[str]]:
            return [tag for tag in tags_data if tag and tag[0] == name]

        id_tag = find_first("d")
        title_tag = find_first("title")
        image_tag = find_first("image")
        summary_tag = find_first("summary")
        location_tag = find_first("location")
        geohash_tag = find_first("g")

        identifier = id_tag[1] if id_tag and len(id_tag) > 1 else ""
        title = title_tag[1] if title_tag and len(title_tag) > 1 else ""

        product_references = [
            prod_tag[1]
            for prod_tag in find_all("a")
            if len(prod_tag) > 1 and prod_tag[1].startswith("30402:")
        ]

        shipping_options = []
        for opt_tag in find_all("shipping_option"):
            entry: Dict[str, Optional[str]] = {}
            if len(opt_tag) > 1:
                entry["reference"] = opt_tag[1]
            if len(opt_tag) > 2:
                entry["extra_cost"] = opt_tag[2]
            shipping_options.append(entry)

        try:
            author = event.author().to_bech32()
        except Exception:
            author = event.author().to_hex()

        return cls(
            id=identifier,
            title=title,
            description=event.content() or "",
            product_references=product_references,
            image=image_tag[1] if image_tag and len(image_tag) > 1 else None,
            summary=summary_tag[1] if summary_tag and len(summary_tag) > 1 else None,
            location=(
                location_tag[1] if location_tag and len(location_tag) > 1 else None
            ),
            geohash=geohash_tag[1] if geohash_tag and len(geohash_tag) > 1 else None,
            shipping_options=shipping_options,
            author=author,
        )


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

        # ------------------------------------------------------------------------------ #
        # Delegation (NIP-26) Support
        # ------------------------------------------------------------------------------ #

        # class Delegation(BaseModel):
        #     """
        #     NIP‑26 delegation wrapper.

        #     A merchant signs a *kind 30078* event delegating publishing rights to the
        #     server.  This helper parses that event, validates its signature and
        #     provides convenience checks for downstream publishing code.
        #     """

        #     author: str  # Merchant pubkey (bech32 or hex)
        #     conditions: str  # Raw query string e.g. "kind=30078&expires_at=…"
        #     sig: str  # Merchant signature
        #     tag: list[str]  # Complete ["delegation", …] tag to re‑attach
        #     created_at: int  # Delegation creation (unix ts)
        #     expires_at: int  # Expiry (unix ts)
        #     allowed_kinds: Set[int]  # Kinds we may publish

        #     # ------------------------------------------------------------------ #
        #     # Construction helpers
        #     # ------------------------------------------------------------------ #
        #     @classmethod
        #     def parse(cls, raw: str | dict) -> "Delegation":
        #         """
        #         Convert raw JSON (str or dict) of a *kind 30078* event into a validated
        #         Delegation instance.

        #         Raises:
        #             ValueError - on wrong kind or bad signature.
        #         """
        #         evt = raw if isinstance(raw, dict) else json.loads(raw)

        #         # Basic integrity checks
        #         if evt.get("kind") != 30078:
        #             raise ValueError("Event is not a delegation (kind 30078)")

        #         # Verify sig using nostr‑sdk
        #         event_obj = Event.from_json(json.dumps(evt))
        #         if not event_obj.verify():
        #             raise ValueError("Invalid delegation signature")

        #         # Pull out the delegation tag parts
        #         tags = evt.get("tags", [])

        #         # Find the delegation tag (should be ["delegation", delegatee, conditions, token])
        #         delegation_tag = None
        #         for tag in tags:
        #             if len(tag) >= 4 and tag[0] == "delegation":
        #                 delegation_tag = tag
        #                 break

        #         if delegation_tag is None:
        #             raise ValueError("Delegation tag missing")

        #         cond_str = delegation_tag[2]  # "kind=0,1,30023&created_at<1751565393"
        #         cond_map = {}

        #         # Parse conditions more flexibly to handle different formats
        #         for condition in cond_str.split("&"):
        #             if "=" in condition:
        #                 k, v = condition.split("=", 1)
        #                 cond_map[k] = v
        #             elif "<" in condition:
        #                 # Handle created_at<timestamp format
        #                 k, v = condition.split("<", 1)
        #                 if k == "created_at":
        #                     cond_map["expires_at"] = (
        #                         v  # created_at<timestamp means expires at timestamp
        #                     )

        #         allowed = set()
        #         if "kind" in cond_map:
        #             allowed = {int(k) for k in cond_map["kind"].split(",") if k.isdigit()}

        #         created = int(cond_map.get("created_at", evt["created_at"]))
        #         expires = int(cond_map.get("expires_at", created))

        #         return cls(
        #             author=evt["pubkey"],
        #             conditions=cond_str,
        #             sig=evt["sig"],
        #             tag=delegation_tag,
        #             created_at=created,
        #             expires_at=expires,
        #             allowed_kinds=allowed,
        #         )

        # ------------------------------------------------------------------ #
        # Validation helpers
        # ------------------------------------------------------------------ #
        # def validate_event(self, event: Event) -> None:
        #     """
        #     Ensure *event* is publishable under this delegation.

        #     Raises:
        #         ValueError - if kind not allowed or delegation expired.
        #     """
        #     event_kind_value = event.kind().as_u16()  # Convert Kind to integer
        #     if event_kind_value not in self.allowed_kinds and self.allowed_kinds:
        #         raise ValueError("Event kind not allowed by delegation")

        #     now_ts = int(datetime.now(timezone.utc).timestamp())
        #     if now_ts > self.expires_at:
        #         raise ValueError("Delegation expired")

        # # Convenience: ready‑made tag to append before publish()
        # @property
        # def delegation_tag(self) -> list[str]:
        #     return self.tag

        # @property
        # def delegatee(self) -> str:
        #     """
        #     Get the delegatee's public key from the delegation tag.

        #     Note: According to NIP-26, the delegatee public key is NOT stored in the
        #     delegation tag. The delegatee is the entity that will use this delegation
        #     to publish events. This property returns empty string as the delegatee
        #     must be determined from context.

        #     Returns:
        #         str: Empty string (delegatee not stored in delegation tag)
        #     """
        #     return ""  # Delegatee not stored in delegation tag per NIP-26

        # @property
        # def delegator(self) -> str:
        #     """
        #     Get the delegator's public key (same as author).

        #     Returns:
        #         str: Public key of the delegator (entity granting delegation rights)
        #     """
        # return self.author
