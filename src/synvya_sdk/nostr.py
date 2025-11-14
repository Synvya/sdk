"""
Core Nostr utilities for agentstr.
"""

import asyncio
import hashlib
import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

import coincurve
import requests

from .models import (
    ClassifiedListing,
    Collection,
    KeyEncoding,
    Namespace,
    NostrKeys,
    Product,
    Profile,
    ProfileFilter,
    Stall,
)

try:
    from nostr_sdk import (
        Alphabet,
        Client,
        Coordinate,
        Event,
        EventBuilder,
        EventDeletionRequest,
        EventId,
        Events,
        Filter,
        HandleNotification,
        JsonValue,
        Keys,
        Kind,
        Metadata,
        MetadataRecord,
        Nip96ServerConfig,
        Nip96UploadRequest,
        Nip96UploadResponse,
        NostrSigner,
        ProductData,
        PublicKey,
        RelayMessage,
        RelayUrl,
        SingleLetterTag,
        Tag,
        TagKind,
    )

except ImportError as exc:
    raise ImportError(
        "`nostr_sdk` not installed. Please install using `pip install nostr_sdk`"
    ) from exc


class NostrClient:
    """
    NostrClient implements the set of Nostr utilities required for
    higher level functions implementations like the Marketplace.

    Initialization involving async calls is handled by an asynchronous
    factory method `create`.
    """

    logger = logging.getLogger("NostrClient")
    _instances_from_create: set[int] = set()

    # ----------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------

    def __init__(
        self,
        relays: Union[str, List[str]],
        private_key: str,
        _from_create: bool = False,
    ) -> None:
        """
        Internal method to initialize the Nostr client.
        SDK users should use the create() method instead.

        Args:
            relays: Nostr relay(s) that the client will connect to.
                    Can be a single URL string or a list of URLs.
            private_key: Private key for the client in hex or bech32 format
        """
        if not _from_create:
            raise RuntimeError("NostrClient must be created using the create() method")

        # Track instance ID
        self._instance_id = id(self)
        NostrClient._instances_from_create.add(self._instance_id)

        # Convert single relay to list for consistent handling
        self.relays: List[str] = [relays] if isinstance(relays, str) else relays
        if not self.relays:
            raise ValueError("At least one relay URL must be provided")

        # Initialize delegations as empty dictionary: merchant_pubkey -> Delegation
        # self.delegations: Dict[str, Delegation] = {}

        self.keys: Keys = Keys.parse(private_key)
        self.nostr_signer: NostrSigner = NostrSigner.keys(self.keys)
        self.client: Client = Client(self.nostr_signer)
        self.connected: bool = False
        self.profile: Optional[Profile] = None  # Initialized asynchronously

        # Set log handling
        if not NostrClient.logger.hasHandlers():
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            NostrClient.logger.addHandler(console_handler)

    def __del__(self) -> None:
        """
        Delete the NostrClient instance.
        """
        if hasattr(self, "_instance_id"):
            NostrClient._instances_from_create.discard(self._instance_id)

    @classmethod
    async def create(
        cls,
        relays: Union[str, List[str]],
        private_key: str,
    ) -> "NostrClient":
        """
        Asynchronous factory method to initialize the Nostr client.
        Use instead of the __init__ method.

        Args:
            relays: Nostr relay(s) that the client will connect to.
                    Can be a single URL string or a list of URLs.
            private_key: Private key for the client in hex or bech32 format

        Returns:
            NostrClient: An initialized NostrClient instance
        """
        instance = cls(relays, private_key, _from_create=True)

        try:
            # Try to download the profile from the relay if it already exists
            instance.profile = await instance.async_get_profile(
                instance.keys.public_key().to_bech32()
            )
        except ValueError:
            # If the profile doesn't exist, create a new one
            instance.profile = Profile(instance.keys.public_key().to_bech32())
        except Exception as e:
            raise RuntimeError(f"Unable to complete async initialization: {e}") from e

        return instance

    async def async_delete_event(
        self, event_id: str, reason: Optional[str] = None
    ) -> str:
        """
        Requests the relay to delete an event. Relays may or may not honor the request.

        Args:
            event_id: Nostr event ID associated with the event to be deleted
            reason: optional reason for deleting the event

        Returns:
            str: id of the event requesting the deletion of event_id

        Raises:
            RuntimeError: if the deletion event can't be published
        """
        try:
            event_id_obj = EventId.parse(event_id)
        except Exception as e:
            raise RuntimeError(f"Invalid event ID: {e}") from e

        if not reason:
            reason = "No reason provided"

        # nostr-sdk has changed the arguments to this method
        # event_builder = EventBuilder.delete(ids=[event_id_obj], reason=reason)
        event_deletion_request = EventDeletionRequest(
            ids=[event_id_obj], coordinates=[], reason=[reason]
        )
        event_builder = EventBuilder.delete(event_deletion_request)

        # return_event_id_obj = await self._async_publish_event(event_builder)
        output = await self.client.send_event_builder(event_builder)

        return str(output.id.to_bech32())

    def delete_event(self, event_id: str, reason: Optional[str] = None) -> str:
        """
        Synchronous wrapper for async_delete_event
        """
        return asyncio.run(self.async_delete_event(event_id, reason))

    async def async_get_agents(self, profile_filter: ProfileFilter) -> set[Profile]:
        """
        Retrieve all agents from the relay that match the filter.
        Agents are defined as profiles (kind:0 events) with bot property set to true
        that also match the ProfileFilter

        Args:
            profile_filter: filter to apply to the results

        Returns:
            set[Profile]: set of agent profiles
        """

        agents: set[Profile] = set()

        if profile_filter is None:
            raise ValueError("Profile filter is required")

        events_filter = (
            Filter()
            .kind(Kind(0))
            .custom_tag(SingleLetterTag.uppercase(Alphabet.L), profile_filter.namespace)
            .custom_tag(SingleLetterTag.lowercase(Alphabet.L), profile_filter.label)
        )
        # hashtags don't work on filters :(
        # events_filter = events_filter.hashtags(["joker"])

        try:
            # events = await self._async_get_events(events_filter)
            events = await self.client.fetch_events_from(
                urls=self._get_relay_urls(),
                filter=events_filter,
                timeout=timedelta(seconds=2),
            )
            if events.len() == 0:
                return agents  # returning empty set
            events_list = events.to_vec()
            for event in events_list:
                profile = await Profile.from_event(event)
                if profile.is_bot() and all(
                    hashtag in profile.get_hashtags()
                    for hashtag in profile_filter.hashtags
                ):
                    agents.add(profile)
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve agents: {e}") from e

        return agents

    def get_agents(self, profile_filter: ProfileFilter) -> set[Profile]:
        """
        Synchronous wrapper for async_get_agents
        """
        return asyncio.run(self.async_get_agents(profile_filter))

    async def async_get_classified_listings(
        self, merchant: str, collection: Optional[Collection] = None
    ) -> List[ClassifiedListing]:
        """
        Retrieve classified listings (kind:30402) for a merchant.

        Args:
            merchant: Merchant public key (hex or bech32)
            collection: Optional collection constraint

        Returns:
            List[ClassifiedListing]: parsed listings
        """

        try:
            merchant_key = PublicKey.parse(merchant)
        except Exception as e:
            raise RuntimeError(f"Invalid merchant key: {e}") from e

        collection_ref: Optional[str] = None
        if collection is not None and collection.id:
            try:
                author_hex = PublicKey.parse(collection.author).to_hex()
            except Exception:
                author_hex = collection.author
            if author_hex:
                collection_ref = f"30405:{author_hex}:{collection.id}"

        try:
            if not self.connected:
                await self._async_connect()

            events_filter = Filter().kind(Kind(30402)).author(merchant_key)
            events = await self.client.fetch_events_from(
                urls=self._get_relay_urls(),
                filter=events_filter,
                timeout=timedelta(seconds=2),
            )
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve classified listings: {e}") from e

        listings: List[ClassifiedListing] = []
        try:
            events_list = events.to_vec()
        except Exception as e:
            self.logger.warning("Failed to get classified listing events: %s", e)
            return []

        for event in events_list:
            try:
                listing = ClassifiedListing.from_event(event)
            except Exception as exc:
                self.logger.warning("Failed to parse classified listing: %s", exc)
                continue

            if collection_ref is not None:
                raw_collections = getattr(listing, "collections", None)
                collections_value: List[str]
                if isinstance(raw_collections, list):
                    collections_value = raw_collections
                elif raw_collections is None:
                    collections_value = []
                else:
                    continue
                if collection_ref not in collections_value:
                    continue
            listings.append(listing)

        return listings

    def get_classified_listings(
        self, merchant: str, collection: Optional[Collection] = None
    ) -> List[ClassifiedListing]:
        """
        Synchronous wrapper for async_get_classified_listings
        """
        return asyncio.run(self.async_get_classified_listings(merchant, collection))

    async def async_get_collections(
        self, merchant: Optional[str] = None
    ) -> List[Collection]:
        """
        Retrieve product collections (kind:30405) for an optional merchant.

        Args:
            merchant: Optional merchant public key (hex or bech32)

        Returns:
            List[Collection]: list of collections
        """

        collections: List[Collection] = []

        if merchant is not None:
            try:
                merchant_key = PublicKey.parse(merchant)
            except Exception as e:
                raise RuntimeError(f"Invalid merchant key: {e}") from e
        else:
            merchant_key = None

        try:
            if not self.connected:
                await self._async_connect()

            events_filter = Filter().kind(Kind(30405))
            if merchant_key is not None:
                events_filter = events_filter.authors([merchant_key])

            events = await self.client.fetch_events_from(
                urls=self._get_relay_urls(),
                filter=events_filter,
                timeout=timedelta(seconds=5),
            )
        except Exception as e:
            self.logger.warning("Unable to retrieve collections: %s", e)
            return []

        try:
            events_list = events.to_vec()
        except Exception as e:
            self.logger.warning("Failed to get collections vector: %s", e)
            return []

        for event in events_list:
            try:
                collection = Collection.from_event(event)
                collections.append(collection)
            except Exception as exc:
                self.logger.warning("Failed to parse collection: %s", exc)
                continue

        return collections

    def get_collections(self, merchant: Optional[str] = None) -> List[Collection]:
        """
        Synchronous wrapper for async_get_collections
        """
        return asyncio.run(self.async_get_collections(merchant))

    async def async_get_merchants(
        self, profile_filter: Optional[ProfileFilter] = None
    ) -> set[Profile]:
        """
        Retrieve all profiles from the relay that match the filter and contain metadata.

        If no ProfileFilter is provided, all Nostr profiles that have published a stall
        (kind:30017 events) are included in the results.

        Args:
            profile_filter: filter to apply to the results

        Returns:
            set[Profile]: set of merchant profiles
            (skips authors with missing metadata)

        Raises:
            RuntimeError: if it can't connect to the relay
        """
        merchants: set[Profile] = set()

        if profile_filter is not None:

            events_filter = (
                Filter()
                .kind(Kind(0))
                .custom_tag(
                    SingleLetterTag.uppercase(Alphabet.L), profile_filter.namespace
                )
                .custom_tag(SingleLetterTag.lowercase(Alphabet.L), profile_filter.label)
            )

            NostrClient.logger.debug("Events filter: %s", events_filter)

            # retrieve all kind 0 events with the filter.
            try:
                # events = await self._async_get_events(events_filter)
                NostrClient.logger.debug("Fetching events")
                events = await self.client.fetch_events(
                    filter=events_filter,
                    timeout=timedelta(seconds=2),
                )
                NostrClient.logger.debug("Events: %s", events)
                if events.len() == 0:
                    NostrClient.logger.debug("No events found")
                    return merchants  # returning empty set
                events_list = events.to_vec()

                for event in events_list:
                    profile = await Profile.from_event(event)
                    NostrClient.logger.debug("Profile: %s", profile)
                    if all(
                        hashtag in profile.get_hashtags()
                        for hashtag in profile_filter.hashtags
                    ):
                        merchants.add(profile)
            except Exception as e:
                raise RuntimeError(f"Failed to retrieve merchants: {e}") from e

            return merchants

        # No filtering is applied, so we search for merchants by identifying
        # profiles that have published at least one stall

        try:
            # Now async_get_stalls returns List[Stall] directly
            stalls = await self.async_get_stalls()

            # Get unique merchant public keys from stalls
            merchant_keys = set()
            for stall in stalls:
                # We need to query events to get the actual author info
                # Use a filter to get the merchant's profile info
                stall_filter = Filter().kind(Kind(30017)).identifier(stall.id)
                stall_events = await self.client.fetch_events_from(
                    urls=self._get_relay_urls(),
                    filter=stall_filter,
                    timeout=timedelta(seconds=2),
                )

                # Skip if no events found
                if stall_events.len() == 0:
                    continue

                for event in stall_events.to_vec():
                    merchant_keys.add(event.author().to_hex())

            # Now fetch the profiles for these merchants
            for key in merchant_keys:
                try:
                    profile = await self.async_get_profile(key)
                    merchants.add(profile)
                except (ValueError, RuntimeError):
                    # Skip profiles that can't be retrieved
                    continue

            return merchants

        except Exception as e:
            raise RuntimeError(f"Failed to retrieve merchants: {e}") from e

    def get_merchants(
        self, profile_filter: Optional[ProfileFilter] = None
    ) -> set[Profile]:
        """
        Synchronous wrapper for async_get_merchants
        """
        return asyncio.run(self.async_get_merchants(profile_filter))

    async def async_get_merchants_in_marketplace(
        self,
        marketplace_owner: str,
        marketplace_name: str,
        profile_filter: Optional[ProfileFilter] = None,
    ) -> set[Profile]:
        """
        Retrieve all merchants from the relay that belong to the marketplace
        and match the filter.

        If no ProfileFilter is provided, all Nostr profiles included in the marketplace
        are included in the results.

        Args:
            marketplace_owner: Nostr public key of the marketplace owner
                               in bech32 or hex format
            marketplace_name: name of the marketplace
            profile_filter: filter to apply to the results

        Returns:
            set[Profile]: set of merchant profiles
            (skips authors with missing metadata)

        Raises:
            ValueError: if the owner key is invalid
            RuntimeError: if the marketplace can't be retrieved
        """
        if profile_filter is not None:
            raise NotImplementedError("Filtering not implemented.")

        # Downloading all merchants in the marketplace

        # Convert owner to PublicKey
        try:
            owner_key = PublicKey.parse(marketplace_owner)
        except Exception as e:
            raise ValueError(f"Invalid owner key: {e}") from e

        events_filter = Filter().kind(Kind(30019)).author(owner_key)
        try:
            # events = await self._async_get_events(events_filter)
            events = await self.client.fetch_events_from(
                urls=self._get_relay_urls(),
                filter=events_filter,
                timeout=timedelta(seconds=2),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve marketplace: {e}") from e

        events_list = events.to_vec()
        merchants_dict: Dict[PublicKey, Profile] = {}

        for event in events_list:
            content = json.loads(event.content())
            if content.get("name") == marketplace_name:
                merchants = content.get("merchants", [])
                for merchant in merchants:
                    try:
                        # public_key = PublicKey.parse(merchant)
                        profile = await self.async_get_profile(merchant)
                        merchants_dict[merchant] = profile
                    except RuntimeError:
                        continue

        return set(merchants_dict.values())

    def get_merchants_in_marketplace(
        self,
        marketplace_owner: str,
        marketplace_name: str,
        profile_filter: Optional[ProfileFilter] = None,
    ) -> set[Profile]:
        """
        Synchronous wrapper for async_get_merchants_in_marketplace
        """
        return asyncio.run(
            self.async_get_merchants_in_marketplace(
                marketplace_owner, marketplace_name, profile_filter
            )
        )

    async def async_get_products(
        self, merchant: str, stall: Optional[Stall] = None
    ) -> List[Product]:
        """
        Retrieve all products from a given merchant.
        Optional stall argument to only retrieve products from a specific stall.

        Args:
            merchant: Public key of the merchant in hex or bech32 format
            stall: Optional stall to retrieve products from

        Returns:
            List[Product]: list of products

        Raises:
            RuntimeError: if the merchant key is invalid
            RuntimeError: if the products can't be retrieved
        """

        # Convert owner to PublicKey
        try:
            merchant_key = PublicKey.parse(merchant)
        except Exception as e:
            raise RuntimeError(f"Invalid merchant key: {e}") from e

        # Retrieve the events associated with the products
        events: Events = None
        products: List[Product] = []

        try:
            if not self.connected:
                await self._async_connect()

            # print(f"Retrieving products from seller: {seller}")
            events_filter = Filter().kind(Kind(30018)).author(merchant_key)
            if stall is not None:
                coordinate_tag = Coordinate(
                    Kind(30017),
                    merchant,
                    stall.id,
                )
                events_filter = events_filter.coordinate(coordinate_tag)
            events = await self.client.fetch_events_from(
                urls=self._get_relay_urls(),
                filter=events_filter,
                timeout=timedelta(seconds=2),
            )
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve stalls: {e}") from e

        # Parse the events into products
        events_list = events.to_vec()
        for event in events_list:
            content = json.loads(event.content())
            tags = event.tags()
            coordinates = tags.coordinates()
            if len(coordinates) > 0:
                seller_public_key = coordinates[0].public_key().to_bech32()
            else:
                seller_public_key = ""
            hashtags = tags.hashtags()
            for hashtag in hashtags:
                NostrClient.logger.debug("Logger Hashtag: %s", hashtag)
            product_data = ProductData(
                id=content.get("id"),
                stall_id=content.get("stall_id"),
                name=content.get("name"),
                description=content.get("description"),
                images=content.get("images", []),
                currency=content.get("currency"),
                price=content.get("price"),
                quantity=content.get("quantity"),
                specs=content.get("specs", {}),
                shipping=content.get("shipping", []),
                # categories=content.get("categories", []),
                categories=hashtags,
            )
            product = Product.from_product_data(product_data)
            product.set_seller(seller_public_key)
            products.append(product)
        return products

    def get_products(
        self, merchant: str, stall: Optional[Stall] = None
    ) -> List[Product]:
        """
        Synchronous wrapper for async_get_products
        """
        return asyncio.run(self.async_get_products(merchant, stall))

    async def async_get_profile(self, public_key: Optional[str] = None) -> Profile:
        """
        Get the Nostr profile of the client if no argument is provided.
        Otherwise, get the Nostr profile of the public key provided as argument.

        Args:
            public_key: optional public key in bech32 or hex format of the profile to retrieve

        Returns:
            Profile: own profile if no argument is provided, otherwise the profile
            of the given public key

        Raises:
            RuntimeError: if the profile can't be retrieved
        """
        if public_key is None:
            assert (
                self.profile is not None
            ), "Profile not initialized. Call create() first."
            return self.profile

        # return await self._async_get_profile_from_relay(PublicKey.parse(public_key))
        try:
            if not self.connected:
                await self._async_connect()
        except RuntimeError as e:
            raise RuntimeError(f"Unable to connect to relay: {e}") from e

        profile_key = PublicKey.parse(public_key)

        try:
            events = await self.client.fetch_events(
                filter=Filter().authors([profile_key]).kind(Kind(0)).limit(1),
                timeout=timedelta(seconds=2),
            )

            if events.len() > 0:
                profile = await Profile.from_event(events.first())
                return profile

            raise ValueError("No kind:0 event found")

        except RuntimeError as e:
            raise RuntimeError(f"Unable to retrieve kind:0 event: {e}") from e

    def get_profile(self, public_key: Optional[str] = None) -> Profile:
        """
        Synchronous wrapper for async_get_profile
        """
        return asyncio.run(self.async_get_profile(public_key))

    async def async_get_stalls(self, merchant: Optional[str] = None) -> List[Stall]:
        """
        Asynchronous function to retrieve the stalls from a relay.
        If a merchant is provided, only the stalls from the merchant are retrieved.

        Args:
            merchant: Optional PublicKey of the merchant to retrieve the stalls for

        Returns:
            List[Stall]: list of stalls

        Raises:
            RuntimeError: if the stalls can't be retrieved
        """
        stalls = []

        if merchant is not None:
            try:
                merchant_key = PublicKey.parse(merchant)
            except Exception as e:
                raise RuntimeError(f"Invalid merchant key: {e}") from e

        # Fetch stall events
        try:
            if not self.connected:
                await self._async_connect()

            events_filter = Filter().kind(Kind(30017))
            if merchant is not None:
                events_filter = events_filter.authors([merchant_key])

            events = await self.client.fetch_events_from(
                urls=self._get_relay_urls(),
                filter=events_filter,
                timeout=timedelta(seconds=5),
            )
        except Exception as e:
            self.logger.warning("Unable to retrieve stalls: %s", e)
            # Return empty list instead of raising exception
            return []

        # Process events even if empty
        try:
            events_list = events.to_vec()
        except Exception as e:
            self.logger.warning("Failed to get events vector: %s", e)
            # Return empty list if we can't get the events vector
            return []

        # Construct stalls
        for event in events_list:
            try:
                # Parse the content field instead of the whole event
                content = event.content()
                # Skip empty content
                if not content or content.isspace():
                    continue

                stall = Stall.from_json(content)
                # Only add valid stalls with an ID
                if stall.id != "unknown":
                    stalls.append(stall)
            except Exception as e:
                self.logger.warning("Failed to parse stall data: %s", e)
                continue

        return stalls

    def get_stalls(self, merchant: Optional[str] = None) -> List[Stall]:
        """
        Synchronous wrapper for async_get_stalls

        Args:
            merchant: Optional PublicKey of the merchant to retrieve the stalls for

        Returns:
            List[Stall]: list of stalls
        """
        return asyncio.run(self.async_get_stalls(merchant))

    async def async_publish_note(self, text: str) -> str:
        """
        Asynchronous funcion to publish kind 1 event (text note) to the relay

        Args:
            text: text to be published as kind 1 event

        Returns:
            str: id of the event publishing the note

        Raises:
            RuntimeError: if the note can't be published
        """
        event_builder = EventBuilder.text_note(text)
        # event_id_obj = await self._async_publish_event(event_builder)
        output = await self.client.send_event_builder(event_builder)
        return str(output.id.to_bech32())

    def publish_note(self, text: str) -> str:
        """
        Synchronous wrapper for async_publish_note
        """
        return asyncio.run(self.async_publish_note(text))

    async def async_receive_message(self, timeout: Optional[int] = 15) -> str:
        """
        Receive one message from the Nostr relay using notifications.
        Uses a proper subscription approach and waits for real-time events.

        Args:
            timeout: Maximum time to wait for a message in seconds

        Returns:
            JSON string containing message details
        """
        if not self.connected:
            try:
                await self._async_connect()
            except Exception as e:
                self.logger.error("Failed to connect: %s", e)
                return json.dumps(
                    {
                        "type": "none",
                        "sender": "none",
                        "content": f"Connection error: {str(e)}",
                    }
                )

        # Default response for no messages
        response = {"type": "none", "sender": "none", "content": "No messages received"}

        try:
            # Initialize event response future
            message_received = asyncio.Future()

            # Important: we need to use BOTH our public key and empty "p" tags to
            # catch all messages
            # Some relays might send private messages without proper targeting
            message_filter = (
                Filter()
                .kinds([Kind(4), Kind(1059)])  # DM and wrapped events
                .pubkey(self.keys.public_key())
                .limit(0)  # Only get new messages
            )

            self.logger.debug(
                "Creating subscription with filter: kinds=[4,1059], pubkey=%s",
                self.keys.public_key().to_bech32(),
            )

            # Create subscription
            subscription = await self.client.subscribe(message_filter, None)
            self.logger.debug("Subscription created: %s", subscription.id)

            # Create a notification handler
            class SingleMessageHandler(HandleNotification):
                def __init__(self, nostr_client, future):
                    super().__init__()
                    self.nostr_client = nostr_client
                    self.future = future
                    self.received_eose = False

                async def handle_msg(self, relay_url: str, msg: RelayMessage) -> None:
                    # Use class-level logger
                    NostrClient.logger.debug("Handle_msg from %s: %s", relay_url, msg)

                    msg_enum = msg.as_enum()

                    # Handle end of stored events
                    if msg_enum.is_end_of_stored_events():
                        NostrClient.logger.debug(
                            "Received EOSE from %s, now waiting for real-time events",
                            relay_url,
                        )
                        self.received_eose = True
                        return

                    # We only care about event messages
                    if not msg_enum.is_event_msg():
                        return

                    event = msg_enum.event
                    NostrClient.logger.debug(
                        "Received event kind %s from %s",
                        event.kind(),
                        event.author().to_bech32(),
                    )

                    # Process based on event kind
                    if event.kind() == Kind(4):
                        NostrClient.logger.debug("Processing DM")
                        try:
                            content = (
                                await self.nostr_client.nostr_signer.nip04_decrypt(
                                    event.author(), event.content()
                                )
                            )
                            NostrClient.logger.debug("Decrypted content: %s", content)
                            if not self.future.done():
                                self.future.set_result(
                                    {
                                        "type": "kind:4",
                                        "sender": event.author().to_bech32(),
                                        "content": content,
                                    }
                                )
                        except Exception as e:
                            NostrClient.logger.error("Failed to decrypt message: %s", e)

                    elif event.kind() == Kind(1059):
                        NostrClient.logger.debug("Processing gift-wrapped message")
                        try:
                            unwrapped = await self.nostr_client.client.unwrap_gift_wrap(
                                event
                            )
                            rumor = unwrapped.rumor()
                            kind_str = f"kind:{rumor.kind().as_u16()}"

                            sender = "unknown"
                            if hasattr(rumor, "author") and callable(
                                getattr(rumor, "author")
                            ):
                                author = rumor.author()
                                if author:
                                    sender = author.to_bech32()

                            NostrClient.logger.debug(
                                "Unwrapped content: %s", rumor.content()
                            )
                            if not self.future.done():
                                self.future.set_result(
                                    {
                                        "type": kind_str,
                                        "sender": sender,
                                        "content": rumor.content(),
                                    }
                                )
                        except Exception as e:
                            NostrClient.logger.error("Failed to unwrap gift: %s", e)

                async def handle(
                    self, relay_url: str, subscription_id: str, event: Event
                ) -> None:
                    NostrClient.logger.debug(
                        "Handle from %s, subscription %s, event %s",
                        relay_url,
                        subscription_id,
                        event.id(),
                    )

                    # Process based on event kind
                    if event.kind() == Kind(4):
                        NostrClient.logger.debug("Processing DM in handle")
                        try:
                            content = (
                                await self.nostr_client.nostr_signer.nip04_decrypt(
                                    event.author(), event.content()
                                )
                            )
                            NostrClient.logger.debug("Decrypted content: %s", content)
                            if not self.future.done():
                                self.future.set_result(
                                    {
                                        "type": "kind:4",
                                        "sender": event.author().to_bech32(),
                                        "content": content,
                                    }
                                )
                        except Exception as e:
                            NostrClient.logger.error("Failed to decrypt message: %s", e)

                    elif event.kind() == Kind(1059):
                        NostrClient.logger.debug(
                            "Processing gift-wrapped message in handle"
                        )
                        try:
                            unwrapped = await self.nostr_client.client.unwrap_gift_wrap(
                                event
                            )
                            rumor = unwrapped.rumor()
                            kind_str = f"kind:{rumor.kind().as_u16()}"

                            sender = "unknown"
                            if hasattr(rumor, "author") and callable(
                                getattr(rumor, "author")
                            ):
                                author = rumor.author()
                                if author:
                                    sender = author.to_bech32()

                            NostrClient.logger.debug(
                                "Unwrapped content: %s", rumor.content()
                            )
                            if not self.future.done():
                                self.future.set_result(
                                    {
                                        "type": kind_str,
                                        "sender": sender,
                                        "content": rumor.content(),
                                    }
                                )
                        except Exception as e:
                            NostrClient.logger.error("Failed to unwrap gift: %s", e)

            # Create handler and notification task
            handler = SingleMessageHandler(self, message_received)

            try:
                # Start notification handling
                self.logger.debug("Starting notification handling")
                notification_task = asyncio.create_task(
                    self.client.handle_notifications(handler)
                )

                # Wait for either a message or timeout
                try:
                    message = await asyncio.wait_for(message_received, timeout=timeout)
                    self.logger.debug("Received message: %s", message)
                    return json.dumps(message)
                except asyncio.TimeoutError:
                    # No message received within timeout
                    self.logger.debug("Timeout waiting for message")
                    return json.dumps(response)

            finally:
                # Clean up
                try:
                    if (
                        "notification_task" in locals()
                        and notification_task
                        and not notification_task.done()
                    ):
                        self.logger.debug("Cancelling notification task")
                        notification_task.cancel()

                    self.logger.debug("Unsubscribing from %s", subscription.id)
                    await self.client.unsubscribe(subscription.id)
                except Exception as e:
                    self.logger.error("Error cleaning up subscription: %s", e)

        except Exception as e:
            self.logger.error("Error in receive_message: %s", e)
            return json.dumps(
                {"type": "none", "sender": "none", "content": f"Error: {str(e)}"}
            )

    def receive_message(self, timeout: Optional[int] = 15) -> str:
        """
        Synchronous wrapper for async_receive_message
        """
        return asyncio.run(self.async_receive_message(timeout))

    async def async_send_message(self, kind: str, key: str, message: str) -> str:
        """
        Sends
        NIP-04 Direct Message `kind:4` to a Nostr public key.
        NIP-17 Direct Message `kind:14` to a Nostr public key.

        Args:
            kind: message kind to use (kind:4 or kind:14)
            key: public key of the recipient in bech32 or hex format
            message: message to send

        Returns:
            str: id of the event publishing the message

        Raises:
            RuntimeError: if the message can't be sent
        """
        # Make sure we're connected to the relay
        if not self.connected:
            await self._async_connect()

        try:
            # Parse the public key first
            public_key = PublicKey.parse(key)

            # Send based on kind
            if kind == "kind:14":
                self.logger.debug("Sending NIP-17 private message")
                output = await self.client.send_private_msg(public_key, message)
            elif kind == "kind:4":
                self.logger.debug("Sending NIP-04 direct message")
                encrypted_message = await self.nostr_signer.nip04_encrypt(
                    public_key=public_key, content=message
                )
                builder = EventBuilder(Kind(4), encrypted_message).tags(
                    [Tag.public_key(public_key)]
                )
                output = await self.client.send_event_builder(builder)
                self.logger.debug(
                    "async_send_message: event id: %s", output.id.to_bech32()
                )
            else:
                self.logger.error("Invalid message kind: %s", kind)
                raise RuntimeError(f"Invalid message kind: {kind}")

            # Check if any relay accepted the message
            if len(output.success) > 0:
                self.logger.info(
                    "Message sent to %s: %s", public_key.to_bech32(), message
                )
                return str(output.id.to_bech32())

            # No relay received the message
            self.logger.error(
                "Message not sent to %s. No relay accepted it.", public_key.to_bech32()
            )
            raise RuntimeError("Unable to send message: No relay accepted it")
        except Exception as e:
            self.logger.error("Failed to send message: %s", str(e))
            raise RuntimeError(f"Unable to send message: {e}") from e

    def send_message(self, kind: str, key: str, message: str) -> str:
        """
        Synchronous wrapper for async_send_message
        """
        return asyncio.run(self.async_send_message(kind, key, message))

    async def async_set_product(self, product: Product) -> str:
        """
        Create or update a NIP-15 Marketplace product with event kind 30018

        Args:
            product: Product to be published

        Returns:
            str: id of the event publishing the product

        Raises:
            RuntimeError: if the product can't be published
        """
        if self.profile is None:
            raise RuntimeError("Profile not initialized. Call create() first.")

        coordinate_tag = Coordinate(
            Kind(30017),
            PublicKey.parse(self.profile.get_public_key()),
            product.stall_id,
        )

        # EventBuilder.product_data() has a bug with tag handling.
        # We use the function to create the content field and discard the eventbuilder
        bad_event_builder = EventBuilder.product_data(product.to_product_data())

        # create an event from bad_event_builder to extract the content -
        # not broadcasted
        bad_event = await self.client.sign_event_builder(bad_event_builder)
        content = bad_event.content()

        event_tags: List[Tag] = []
        for category in product.categories:
            event_tags.append(Tag.hashtag(category))

        event_tags.append(Tag.identifier(product.id))
        event_tags.append(Tag.coordinate(coordinate_tag))

        # build a new event with the right tags and the content
        # good_event_builder = EventBuilder(Kind(30018), content).tags(
        #     [Tag.identifier(product.id), Tag.coordinate(coordinate_tag)]
        # )

        good_event_builder = EventBuilder(Kind(30018), content).tags(event_tags)

        try:
            output = await self.client.send_event_builder(good_event_builder)
            return str(output.id.to_bech32())
        except Exception as e:
            NostrClient.logger.error(
                "Unable to publish product %s: %s", product.name, e
            )
            raise RuntimeError(f"Unable to publish product {product.name}: {e}") from e

    def set_product(self, product: Product) -> str:
        """
        Synchronous wrapper for async_set_product
        """
        return asyncio.run(self.async_set_product(product))

    async def async_set_profile(self, profile: Profile) -> str:
        """
        Sets the properties of the profile associated with the Nostr client.
        The public key of profile must match the private key of the Nostr client
        The profile is automatically published to the relay.

        Args:
            profile: Profile object with new properties

        Returns:
            str: id of the event publishing the profile

        Raises:
            RuntimeError: if the profile can't be published
            ValueError: if the public key of the profile does not match the private
            key of the Nostr client
        """
        NostrClient.logger.debug("Setting profile: %s", profile)
        # Validate public key ownership or delegation
        client_pubkey = self.keys.public_key().to_hex()
        profile_pubkey = profile.get_public_key(KeyEncoding.HEX)

        # Check if profile belongs to client
        if profile_pubkey != client_pubkey:
            raise ValueError(
                "Public key of the profile does not match the private key of the Nostr client "
            )

        self.profile = profile

        if (name := profile.get_name()) == "":
            raise ValueError("A profile must have a value for the field `name`.")

        # Prepare custom fields
        custom_fields = {}
        if (bot := profile.is_bot()) != "":
            custom_fields["bot"] = JsonValue.BOOL(bot)
        if (environment := profile.get_environment()) != "":
            custom_fields["environment"] = JsonValue.STR(environment)

        # Create MetadataRecord with all fields
        metadata_record = MetadataRecord(
            name=name,
            about=profile.get_about() if profile.get_about() != "" else None,
            banner=profile.get_banner() if profile.get_banner() != "" else None,
            display_name=(
                profile.get_display_name() if profile.get_display_name() != "" else None
            ),
            nip05=profile.get_nip05() if profile.get_nip05() != "" else None,
            picture=profile.get_picture() if profile.get_picture() != "" else None,
            website=profile.get_website() if profile.get_website() != "" else None,
            custom=custom_fields if custom_fields else None,
        )

        # Create Metadata from record
        metadata_content = Metadata.from_record(metadata_record)

        event_builder = EventBuilder.metadata(metadata_content)

        # Build tags list with qualified labels
        tags_list = []

        # Add label tags (lowercase l) as qualified labels: ["l", "<namespace:label>"]
        # This minimizes search load by fully qualifying labels
        labels = profile.labels
        for namespace, labels_list in labels.items():
            for label in labels_list:
                qualified_label = f"{namespace}:{label}"
                tags_list.append(
                    Tag.custom(
                        TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L)),
                        [qualified_label],
                    )
                )

        event_builder = event_builder.tags(tags_list)

        if (email := profile.get_email()) != "":
            event_builder = event_builder.tags(
                [
                    Tag.custom(
                        TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                        [
                            f"email:{email}",
                            "",
                        ],
                    ),
                ]
            )

        if (phone := profile.get_phone()) != "":
            event_builder = event_builder.tags(
                [
                    Tag.custom(
                        TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                        [f"phone:{phone}", ""],
                    ),
                ]
            )

        # Address tags using schema.org PostalAddress format (NIP-73)
        address_tags = []
        if (street := profile.get_street()) != "":
            address_tags.append(
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    [
                        f"postalAddress:streetAddress:{street}",
                        "https://schema.org/streetAddress",
                    ],
                )
            )
        if (city := profile.get_city()) != "":
            address_tags.append(
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    [
                        f"postalAddress:addressLocality:{city}",
                        "https://schema.org/addressLocality",
                    ],
                )
            )
        if (state := profile.get_state()) != "":
            address_tags.append(
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    [
                        f"postalAddress:addressRegion:{state}",
                        "https://schema.org/addressRegion",
                    ],
                )
            )
        if (zip_code := profile.get_zip_code()) != "":
            address_tags.append(
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    [
                        f"postalAddress:postalCode:{zip_code}",
                        "https://schema.org/postalCode",
                    ],
                )
            )
        if (country := profile.get_country()) != "":
            address_tags.append(
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    [
                        f"postalAddress:addressCountry:{country}",
                        "https://schema.org/addressCountry",
                    ],
                )
            )

        if address_tags:
            event_builder = event_builder.tags(address_tags)

        if (geohash := profile.get_geohash()) != "":
            event_builder = event_builder.tags(
                [
                    Tag.custom(
                        TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.G)),
                        [geohash],
                    ),
                ]
            )

        event_builder = event_builder.tags(
            [Tag.hashtag(hashtag) for hashtag in profile.get_hashtags()]
        )

        try:
            # event_id_obj = await self._async_publish_event(event_builder)
            output = await self.client.send_event_builder(event_builder)
            return str(output.id.to_hex())
        except RuntimeError as e:
            raise RuntimeError(f"Failed to publish profile: {e}") from e

    def set_profile(self, profile: Profile) -> str:
        """
        Synchronous wrapper for async_set_profile
        """
        return asyncio.run(self.async_set_profile(profile))

    async def async_set_stall(self, stall: Stall) -> str:
        """
        Asynchronous function to create or update a NIP-15
        Marketplace stall with event kind 30017

        Args:
            stall: Stall to be published

        Returns:
            EventId: Id of the publication event

        Raises:
            RuntimeError: if the Stall can't be published
        """

        event_builder = EventBuilder.stall_data(stall.to_stall_data()).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.G)),
                    [stall.geohash],
                ),
            ]
        )
        # event_id_obj = await self._async_publish_event(event_builder)
        output = await self.client.send_event_builder(event_builder)
        return str(output.id.to_bech32())

    def set_stall(self, stall: Stall) -> str:
        """
        Synchronous wrapper for async_set_stall
        """
        return asyncio.run(self.async_set_stall(stall))

    async def async_subscribe_to_messages(self) -> str:
        """
        Subscribes to messages from the relay.
        """
        subscription = await self.client.subscribe_to(
            self.relays,
            Filter().kinds([Kind(14)]),
        )

        if len(subscription.success) > 0:
            return "success"
        return "error"

    def subscribe_to_messages(self) -> str:
        """
        Synchronous wrapper for async_subscribe_to_messages
        """
        return asyncio.run(self.async_subscribe_to_messages())

    async def async_nip96_upload(
        self,
        server_url: str,
        file_data: bytes,
        mime_type: Optional[str] = None,
        plan: Optional[str] = None,
    ) -> str:
        """
        Upload a file to a NIP-96 compatible server.

        Args:
            server_url: URL of the NIP-96 compatible server
            file_data: Binary data of the file to upload
            mime_type: Optional MIME type of the file
            plan: Optional plan name to use (defaults to "free" if available)

        Returns:
            str: URL of the uploaded file

        Raises:
            RuntimeError: if the file upload fails or plan is not available
        """
        # obtain the server configuration from NIP-96 well-known endpoint
        config_url = f"{server_url.rstrip('/')}/.well-known/nostr/nip96.json"
        try:
            config_response = requests.get(config_url, timeout=10)
            config_response.raise_for_status()  # Raise an exception for HTTP errors
            server_config = Nip96ServerConfig.from_json(config_response.text)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to get server configuration: {e}") from e

        NostrClient.logger.debug("Server json file %s", config_response.text)

        # Select plan: default to "free" if not specified
        selected_plan = plan if plan is not None else "free"

        # Check if the plan exists in server configuration
        server_config_dict = json.loads(config_response.text)
        available_plans = server_config_dict.get("plans", {})

        if selected_plan not in available_plans:
            if plan is None:
                # User didn't specify a plan and "free" doesn't exist
                available_plan_names = list(available_plans.keys())
                raise RuntimeError(
                    f"No 'free' plan available on server. Available plans: {available_plan_names}. "
                    f"Please specify a plan using the 'plan' parameter."
                )
            else:
                # User specified a plan that doesn't exist
                available_plan_names = list(available_plans.keys())
                raise RuntimeError(
                    f"Plan '{selected_plan}' not available on server. "
                    f"Available plans: {available_plan_names}"
                )

        NostrClient.logger.debug("Using plan: %s", selected_plan)

        request = await Nip96UploadRequest.create(
            signer=self.nostr_signer, config=server_config, file_data=file_data
        )

        NostrClient.logger.debug("Request %s", request)

        try:
            auth_header = request.authorization()
            url = request.url()

            # Prepare multipart form data for file upload
            files = {
                "file": ("upload", file_data, mime_type or "application/octet-stream")
            }
            headers = {
                "Authorization": auth_header,
            }
            # Don't set Content-Type header - requests will set it automatically for multipart

            upload = requests.post(url, headers=headers, files=files, timeout=10)
            upload.raise_for_status()
            NostrClient.logger.debug("Upload response %s", upload.text)
            upload_response = Nip96UploadResponse.from_json(upload.text)
            if upload_response.is_success():
                return upload_response.download_url()
            else:
                raise RuntimeError(
                    f"Failed to upload file: {upload_response.message()}"
                )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to upload file: {e}") from e

    def nip96_upload(
        self,
        server_url: str,
        file_data: bytes,
        mime_type: Optional[str] = None,
        plan: Optional[str] = None,
    ) -> str:
        """
        Synchronous wrapper for async_nip96_upload

        Args:
            server_url: URL of the NIP-96 compatible server
            file_data: Binary data of the file to upload
            mime_type: Optional MIME type of the file
            plan: Optional plan name to use (defaults to "free" if available)

        Returns:
            str: URL of the uploaded file
        """
        return asyncio.run(
            self.async_nip96_upload(
                server_url=server_url,
                file_data=file_data,
                mime_type=mime_type,
                plan=plan,
            )
        )

    # ----------------------------------------------------------------
    # Class methods
    # ----------------------------------------------------------------

    @classmethod
    def set_logging_level(cls, logging_level: int) -> None:
        """Set the logging level for the NostrClient logger.

        Args:
            logging_level: The logging level (e.g., logging.DEBUG, logging.INFO)
        """
        cls.logger.setLevel(logging_level)
        for handler in cls.logger.handlers:
            handler.setLevel(logging_level)
        # cls.logger.info("Logging level set to %s", logging.getLevelName(logging_level))

    # ----------------------------------------------------------------
    # internal async functions.
    # Developers should use synchronous functions above
    # ----------------------------------------------------------------

    def _get_relay_urls(self) -> List[RelayUrl]:
        """
        Convert string relay URLs to RelayUrl objects.

        Returns:
            List[RelayUrl]: converted relay URLs
        """
        return [RelayUrl.parse(relay) for relay in self.relays]

    async def _async_connect(self) -> None:
        """
        Asynchronous function to add relays to the NostrClient
        instance and connect to them.

        Raises:
            RuntimeError: if the relay(s) can't be connected to
        """
        if not self.connected:
            try:
                # Add all relays to the client
                for relay in self.relays:
                    relay_url = RelayUrl.parse(relay)
                    await self.client.add_relay(relay_url)
                    NostrClient.logger.info("Relay %s successfully added.", relay)

                # Connect to all relays
                await self.client.connect()
                await asyncio.sleep(2)  # give time for slower connections
                NostrClient.logger.info("Connected to relays: %s", self.relays)
                self.connected = True
            except Exception as e:
                raise RuntimeError(
                    f"Unable to connect to relays {self.relays}. Exception: {e}."
                ) from e


def verify_signature(message: str, signature: str, public_key: str) -> bool:
    """
    Verifies a schnorr signature against a message using a public key.

    This function implements proper cryptographic verification using secp256k1
    schnorr signature verification against the SHA256 hash of the message.

    Args:
        message: The original message that was signed (e.g., "nostr-auth:1703123456")
        signature: The signature in hex format (128 characters)
        public_key: The public key in bech32 or hex format

    Returns:
        bool: True if the signature is cryptographically valid, False otherwise

    Raises:
        ImportError: If secp256k1 library is not installed
        RuntimeError: If proper Schnorr verification is not available
    """

    try:
        # Parse and validate the public key using nostr_sdk
        pubkey = PublicKey.parse(public_key)
        pubkey_hex = pubkey.to_hex()

        # Validate signature format (should be 128 hex characters for schnorr)
        if not signature or len(signature) != 128:
            return False

        # Convert signature from hex to bytes
        try:
            sig_bytes = bytes.fromhex(signature)
        except ValueError:
            return False

        # Convert public key from hex to bytes (remove 0x prefix if present)
        if pubkey_hex.startswith("0x"):
            pubkey_hex = pubkey_hex[2:]
        pubkey_bytes = bytes.fromhex(pubkey_hex)

        # Hash the message with SHA256 (standard for Nostr/Bitcoin signatures)
        message_hash = hashlib.sha256(message.encode("utf-8")).digest()

        # Create secp256k1 public key object
        try:
            # secp256k1 expects 33-byte compressed public key
            # Nostr uses 32-byte x-only public keys, so we need to add the prefix
            if len(pubkey_bytes) == 32:
                # Add the compressed public key prefix (0x02 for even y-coordinate)
                # In practice, we assume even y-coordinate for x-only keys
                compressed_pubkey = b"\x02" + pubkey_bytes
            else:
                compressed_pubkey = pubkey_bytes

            secp_pubkey = coincurve.PublicKey(compressed_pubkey)
        except Exception:
            return False

        # Verify the schnorr signature
        try:
            # For schnorr signatures, we need to use the schnorr verification
            # Note: secp256k1-py might not have direct schnorr support

            # Try schnorr verification if available
            if hasattr(secp_pubkey, "schnorr_verify"):
                return secp_pubkey.schnorr_verify(sig_bytes, message_hash)
            else:
                # No proper Schnorr verification available
                raise RuntimeError(
                    "Proper Schnorr signature verification is not available. "
                    "This function requires a library that supports Schnorr signatures."
                )

        except RuntimeError:
            # Re-raise RuntimeError for missing Schnorr support
            raise
        except Exception:
            return False

    except RuntimeError:
        # Re-raise RuntimeError for missing Schnorr support
        raise
    except Exception:
        # Any parsing or verification error means invalid signature
        return False


def generate_keys(env_var: str, env_path: Path) -> NostrKeys:
    """
    Generates new nostr keys.
    Saves the private key in bech32 format to the .env file.

    Args:
        env_var: Name of the environment variable to store the key
        env_path: Path to the .env file. If None, looks for .env in current directory

    Returns:
        tuple[str, str]: [public key, private key] in bech32 format
    """
    # Generate new keys
    nostr_keys = NostrKeys()
    nsec = nostr_keys.get_private_key(KeyEncoding.BECH32)
    # Determine .env path
    if env_path is None:
        env_path = Path.cwd() / ".env"

    # Read existing .env content
    env_content = ""
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            env_content = f.read()

    # Check if the env var already exists
    lines = env_content.splitlines()
    new_lines = []
    var_found = False

    for line in lines:
        if line.startswith(f"{env_var}="):
            new_lines.append(f"{env_var}={nsec}")
            var_found = True
        else:
            new_lines.append(line)

    # If var wasn't found, add it
    if not var_found:
        new_lines.append(f"{env_var}={nsec}")

    # Write back to .env
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
        if new_lines:  # Add final newline if there's content
            f.write("\n")

    return nostr_keys
