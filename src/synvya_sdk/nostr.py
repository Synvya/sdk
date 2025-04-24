"""
Core Nostr utilities for agentstr.
"""

import asyncio
import json
import logging
import time
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .models import Namespace, NostrKeys, Product, Profile, ProfileFilter, Stall

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
        NostrSigner,
        ProductData,
        PublicKey,
        RelayMessage,
        SingleLetterTag,
        Tag,
        TagKind,
        Timestamp,
        UnsignedEvent,
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

    Nostr is an asynchronous communication protocol. To hide this,
    NostrClient exposes synchronous functions. Users of the NostrClient
    should ignore `_async_` functions which are for internal purposes only.
    """

    logger = logging.getLogger("NostrClient")
    _instances_from_create: set[int] = set()

    # ----------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------

    def __init__(
        self, relay: str, private_key: str, _from_create: bool = False
    ) -> None:
        """
        Initialize the Nostr client.

        Args:
            relay: Nostr relay that the client will connect to
            private_key: Private key for the client in hex or bech32 format
        """
        if not _from_create:
            raise RuntimeError("NostrClient must be created using the create() method")

        # Track instance ID
        self._instance_id = id(self)
        NostrClient._instances_from_create.add(self._instance_id)

        self.relay: str = relay
        self.keys: Keys = Keys.parse(private_key)
        self.nostr_signer: NostrSigner = NostrSigner.keys(self.keys)
        self.client: Client = Client(self.nostr_signer)
        self.connected: bool = False
        # self.stop_event: asyncio.Event = asyncio.Event()
        # self.notification_task: Optional[asyncio.Task] = None
        # self.received_eose: bool = False
        # self.private_message: Optional[UnsignedEvent] = None
        # self.private_gift_wrapped_message: Optional[Event] = None
        # self.direct_message: Optional[Event] = None
        # self.last_message_time: float = 0
        self.profile: Optional[Profile] = None  # Initialized asynchronously
        # self.background_task: Optional[asyncio.Task] = None

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
    async def create(cls, relay: str, private_key: str) -> "NostrClient":
        """
        Asynchronous factory method for proper initialization.
        Use instead of the __init__ method.
        """
        instance = cls(relay, private_key, _from_create=True)

        # Set the initial timestamp within a running loop
        # instance.last_message_time = asyncio.get_running_loop().time()

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
        Agents are defined as profiles with kind:0 bot property set to true
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
            .custom_tag(
                SingleLetterTag.lowercase(Alphabet.L), profile_filter.profile_type
            )
        )
        # hashtags don't work on filters :(
        # events_filter = events_filter.hashtags(["joker"])

        try:
            # events = await self._async_get_events(events_filter)
            events = await self.client.fetch_events_from(
                urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
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

    async def async_get_merchants(
        self, profile_filter: Optional[ProfileFilter] = None
    ) -> set[Profile]:
        """
        Retrieve all merchants from the relay that match the filter.

        If no ProfileFilter is provided, all Nostr profiles that have published a stall
        are included in the results.

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
            if profile_filter.namespace != Namespace.MERCHANT:
                raise ValueError(
                    f"Profile filter namespace must be {Namespace.MERCHANT}"
                )

            events_filter = (
                Filter()
                .kind(Kind(0))
                .custom_tag(
                    SingleLetterTag.uppercase(Alphabet.L), profile_filter.namespace
                )
                .custom_tag(
                    SingleLetterTag.lowercase(Alphabet.L), profile_filter.profile_type
                )
            )

            # retrieve all kind 0 events with the filter.
            try:
                # events = await self._async_get_events(events_filter)
                events = await self.client.fetch_events_from(
                    urls=[self.relay],
                    filter=events_filter,
                    timeout=timedelta(seconds=2),
                )
                if events.len() == 0:
                    return merchants  # returning empty set
                events_list = events.to_vec()
                for event in events_list:
                    profile = await Profile.from_event(event)
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
                    urls=[self.relay], filter=stall_filter, timeout=timedelta(seconds=2)
                )

                # Skip if no events found
                if stall_events.len() == 0:
                    continue

                for event in stall_events.to_vec():
                    merchant_keys.add(event.author().to_bech32())

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
                urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
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
                urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
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

            profile_key = PublicKey.parse(public_key)

            # retrieve standard metadata
            metadata = await self.client.fetch_metadata(
                public_key=profile_key, timeout=timedelta(seconds=2)
            )

            if metadata is None:
                raise RuntimeError("async_get_profile: Unable to retrieve metadata")

            # Create profile from standard metadata
            profile = await Profile.from_metadata(metadata, profile_key.to_bech32())

            # retreive raw event for non-standard metadata
            events = await self.client.fetch_events(
                filter=Filter().authors([profile_key]).kind(Kind(0)).limit(1),
                timeout=timedelta(seconds=2),
            )
            if events.len() > 0:
                tags = events.first().tags()

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
            return profile
        except RuntimeError as e:
            raise RuntimeError(f"Unable to connect to relay: {e}") from e
        except Exception as e:
            raise ValueError(f"Unable to retrieve metadata: {e}") from e

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
                urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=5)
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

            # Important: we need to use BOTH our public key and empty "p" tags to catch all messages
            # Some relays might send private messages without proper targeting
            message_filter = (
                Filter()
                .kinds([Kind(4), Kind(1059)])  # DM and wrapped events
                .pubkey(self.keys.public_key())
                .limit(0)  # Only get new messages
            )

            self.logger.debug(
                f"Creating subscription with filter: kinds=[4,1059], pubkey={self.keys.public_key().to_bech32()}"
            )

            # Create subscription
            subscription = await self.client.subscribe(message_filter, None)
            self.logger.debug(f"Subscription created: {subscription.id}")

            # Create a notification handler
            class SingleMessageHandler(HandleNotification):
                def __init__(self, nostr_client, future):
                    super().__init__()
                    self.nostr_client = nostr_client
                    self.future = future
                    self.received_eose = False

                async def handle_msg(self, relay_url: str, msg: RelayMessage) -> None:
                    # Use class-level logger
                    NostrClient.logger.debug(f"Handle_msg from {relay_url}: {msg}")

                    msg_enum = msg.as_enum()

                    # Handle end of stored events
                    if msg_enum.is_end_of_stored_events():
                        NostrClient.logger.debug(
                            f"Received EOSE from {relay_url}, now waiting for real-time events"
                        )
                        self.received_eose = True
                        return

                    # We only care about event messages
                    if not msg_enum.is_event_msg():
                        return

                    event = msg_enum.event
                    NostrClient.logger.debug(
                        f"Received event kind {event.kind()} from {event.author().to_bech32()}"
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
                            NostrClient.logger.debug(f"Decrypted content: {content}")
                            if not self.future.done():
                                self.future.set_result(
                                    {
                                        "type": "kind:4",
                                        "sender": event.author().to_bech32(),
                                        "content": content,
                                    }
                                )
                        except Exception as e:
                            NostrClient.logger.error(f"Failed to decrypt message: {e}")

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
                                f"Unwrapped content: {rumor.content()}"
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
                            NostrClient.logger.error(f"Failed to unwrap gift: {e}")

                async def handle(
                    self, relay_url: str, subscription_id: str, event: Event
                ) -> None:
                    NostrClient.logger.debug(
                        f"Handle from {relay_url}, subscription {subscription_id}, event {event.id()}"
                    )

                    # Process based on event kind
                    if event.kind() == Kind(4):
                        NostrClient.logger.debug(f"Processing DM in handle")
                        try:
                            content = (
                                await self.nostr_client.nostr_signer.nip04_decrypt(
                                    event.author(), event.content()
                                )
                            )
                            NostrClient.logger.debug(f"Decrypted content: {content}")
                            if not self.future.done():
                                self.future.set_result(
                                    {
                                        "type": "kind:4",
                                        "sender": event.author().to_bech32(),
                                        "content": content,
                                    }
                                )
                        except Exception as e:
                            NostrClient.logger.error(f"Failed to decrypt message: {e}")

                    elif event.kind() == Kind(1059):
                        NostrClient.logger.debug(
                            f"Processing gift-wrapped message in handle"
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
                                f"Unwrapped content: {rumor.content()}"
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
                            NostrClient.logger.error(f"Failed to unwrap gift: {e}")

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
                    self.logger.debug(f"Received message: {message}")
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

                    self.logger.debug(f"Unsubscribing from {subscription.id}")
                    await self.client.unsubscribe(subscription.id)
                except Exception as e:
                    self.logger.error(f"Error cleaning up subscription: {e}")

        except Exception as e:
            self.logger.error(f"Error in receive_message: {e}")
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
        The public key of profile must match the private key of the Nostr client.
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
        if profile.get_public_key() != self.keys.public_key().to_bech32():
            raise ValueError(
                "Public key of the profile does not match the private key of the Nostr client"
            )

        self.profile = profile

        metadata_content = Metadata()
        if (name := self.profile.get_name()) == "":
            raise ValueError("A profile must have a value for the field `name`.")

        metadata_content = metadata_content.set_name(name)
        if (about := self.profile.get_about()) != "":
            metadata_content = metadata_content.set_about(about)
        if (banner := self.profile.get_banner()) != "":
            metadata_content = metadata_content.set_banner(banner)
        if (display_name := self.profile.get_display_name()) != "":
            metadata_content = metadata_content.set_display_name(display_name)
        if (nip05 := self.profile.get_nip05()) != "":
            metadata_content = metadata_content.set_nip05(nip05)
        if (picture := self.profile.get_picture()) != "":
            metadata_content = metadata_content.set_picture(picture)
        if (website := self.profile.get_website()) != "":
            metadata_content = metadata_content.set_website(website)
        if (bot := self.profile.is_bot()) != "":
            metadata_content = metadata_content.set_custom_field(
                key="bot", value=JsonValue.BOOL(bot)
            )

        event_builder = EventBuilder.metadata(metadata_content)

        event_builder = event_builder.tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.uppercase(Alphabet.L)),
                    [self.profile.get_namespace()],
                ),
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L)),
                    [
                        self.profile.get_profile_type(),
                        self.profile.get_namespace(),
                    ],
                ),
            ]
        )

        event_builder = event_builder.tags(
            [Tag.hashtag(hashtag) for hashtag in self.profile.get_hashtags()]
        )

        try:
            # event_id_obj = await self._async_publish_event(event_builder)
            output = await self.client.send_event_builder(event_builder)
            return str(output.id.to_bech32())
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
            [self.relay],
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

    async def _async_connect(self) -> None:
        """
        Asynchronous function to add relay to the NostrClient
        instance and connect to it.


        Raises:
            RuntimeError: if the relay can't be connected to
        """

        if not self.connected:
            try:
                await self.client.add_relay(self.relay)
                NostrClient.logger.info("Relay %s successfully added.", self.relay)
                await self.client.connect()
                await asyncio.sleep(2)  # give time for slower connections
                NostrClient.logger.info("Connected to relay.")
                self.connected = True
            except Exception as e:
                raise RuntimeError(
                    f"Unable to connect to relay {self.relay}. Exception: {e}."
                ) from e

    # async def _async_get_events(self, events_filter: Filter) -> Events:
    #     """
    #     Asynchronous function to retrieve events from the relay

    #     Args:
    #         events_filter: Filter to apply to the events

    #     Returns:
    #         Events: list of events

    #     Raises:
    #         RuntimeError: if the events can't be retrieved
    #     """
    #     try:
    #         if not self.connected:
    #             await self._async_connect()

    #         events = await self.client.fetch_events_from(
    #             urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
    #         )
    #         return events
    #     except Exception as e:
    #         raise RuntimeError(f"Unable to retrieve stalls: {e}") from e

    # async def _async_get_products_events(
    #     self, merchant: PublicKey, stall: Optional[Stall] = None
    # ) -> Events:
    #     """
    #     Asynchronous function to retrieve the products for a given merchant

    #     Args:
    #         merchant: PublicKey of the merchant
    #         stall: Optional Stall to filter products by
    #     Returns:
    #         Events: list of events containing the products of the merchant

    #     Raises:
    #         RuntimeError: if the products can't be retrieved
    #     """
    #     try:
    #         if not self.connected:
    #             await self._async_connect()

    #         # print(f"Retrieving products from seller: {seller}")
    #         events_filter = Filter().kind(Kind(30018)).author(merchant)
    #         if stall is not None:
    #             coordinate_tag = Coordinate(
    #                 Kind(30017),
    #                 merchant,
    #                 stall.id,
    #             )
    #             events_filter = events_filter.coordinate(coordinate_tag)
    #         events = await self.client.fetch_events_from(
    #             urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
    #         )
    #         return events
    #     except Exception as e:
    #         raise RuntimeError(f"Unable to retrieve stalls: {e}") from e

    # async def _async_get_profile_from_relay(self, profile_key: PublicKey) -> Profile:
    #     """
    #     Asynchronous function to retrieve from the Nostr relay the profile
    #     for a given author

    #     Args:
    #         profile_key: PublicKey of the profile to retrieve

    #     Returns:
    #         Profile: profile associated with the public key

    #     Raises:
    #         RuntimeError: if it can't connect to the relay
    #         ValueError: if a profile is not found
    #     """
    #     try:
    #         if not self.connected:
    #             await self._async_connect()

    #         metadata = await self.client.fetch_metadata(
    #             public_key=profile_key, timeout=timedelta(seconds=2)
    #         )
    #         profile = await Profile.from_metadata(metadata, profile_key.to_bech32())
    #         events = await self.client.fetch_events(
    #             filter=Filter().authors([profile_key]).kind(Kind(0)).limit(1),
    #             timeout=timedelta(seconds=2),
    #         )
    #         if events.len() > 0:
    #             tags = events.first().tags()

    #             hashtag_list = tags.hashtags()
    #             for hashtag in hashtag_list:
    #                 profile.add_hashtag(hashtag)

    #             namespace_tag = tags.find(
    #                 TagKind.SINGLE_LETTER(SingleLetterTag.uppercase(Alphabet.L))
    #             )
    #             if namespace_tag is not None:
    #                 profile.set_namespace(namespace_tag.content())

    #             profile_type_tag = tags.find(
    #                 TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L))
    #             )
    #             if profile_type_tag is not None:
    #                 profile.set_profile_type(profile_type_tag.content())
    #         return profile
    #     except RuntimeError as e:
    #         raise RuntimeError(f"Unable to connect to relay: {e}") from e
    #     except Exception as e:
    #         raise ValueError(f"Unable to retrieve metadata: {e}") from e

    # async def _async_get_profile_from_relay2(self, profile_key: PublicKey) -> Profile:
    #     """
    #     Asynchronous function to retrieve from the Nostr relay the profile
    #     for a given author

    #     Args:
    #         profile_key: PublicKey of the profile to retrieve

    #     Returns:
    #         Profile: profile associated with the public key

    #     Raises:
    #         RuntimeError: if it can't connect to the relay
    #         ValueError: if a profile is not found
    #     """
    #     try:
    #         if not self.connected:
    #             await self._async_connect()

    #         profile_filter = Filter().kind(Kind(0)).authors([profile_key]).limit(1)
    #         events = await self.client.fetch_events_from(
    #             urls=[self.relay], filter=profile_filter, timeout=timedelta(seconds=2)
    #         )
    #         if events.len() > 0:
    #             # process kind:0 event
    #             profile = await Profile.from_event(events.first())
    #             return profile
    #         raise ValueError("Profile not found")

    #     except RuntimeError as e:
    #         raise RuntimeError(f"Unable to connect to relay: {e}") from e
    #     except Exception as e:
    #         raise ValueError(f"Unable to retrieve profile: {e}") from e

    # async def _async_publish_event(self, event_builder: EventBuilder) -> EventId:
    #     """
    #     Publish generic Nostr event to the relay

    #     Returns:
    #         EventId: event id of the published event

    #     Raises:
    #         RuntimeError: if the event can't be published
    #     """
    #     try:
    #         if not self.connected:
    #             await self._async_connect()

    #         # Wait for connection and try to publish
    #         output = await self.client.send_event_builder(event_builder)

    #         # More detailed error handling
    #         if not output:
    #             raise RuntimeError("No output received from send_event_builder")
    #         if len(output.success) == 0:
    #             reason = getattr(output, "message", "unknown")
    #             raise RuntimeError(f"Event rejected by relay. Reason: {reason}")

    #         NostrClient.logger.debug(
    #             "Event published with event id: %s", output.id.to_bech32()
    #         )
    #         return output.id

    #     except Exception as e:
    #         NostrClient.logger.error("Failed to publish event: %s", str(e))
    #         NostrClient.logger.debug("Event details:", exc_info=True)
    #         raise RuntimeError(f"Unable to publish event: {str(e)}") from e

    # async def _async_set_profile(self) -> EventId:
    #     """
    #     Asynchronous function to publish a Nostr profile with event kind 0

    #     Returns:
    #         EventId: event id if successful

    #     Raises:
    #         RuntimeError: if the profile can't be published
    #         ValueError: if the mandatory field `name` is missing
    #     """

    #     metadata_content = Metadata()
    #     if (name := self.profile.get_name()) == "":
    #         raise ValueError("A profile must have a value for the field `name`.")

    #     metadata_content = metadata_content.set_name(name)
    #     if (about := self.profile.get_about()) != "":
    #         metadata_content = metadata_content.set_about(about)
    #     if (banner := self.profile.get_banner()) != "":
    #         metadata_content = metadata_content.set_banner(banner)
    #     if (display_name := self.profile.get_display_name()) != "":
    #         metadata_content = metadata_content.set_display_name(display_name)
    #     if (nip05 := self.profile.get_nip05()) != "":
    #         metadata_content = metadata_content.set_nip05(nip05)
    #     if (picture := self.profile.get_picture()) != "":
    #         metadata_content = metadata_content.set_picture(picture)
    #     if (website := self.profile.get_website()) != "":
    #         metadata_content = metadata_content.set_website(website)
    #     if (bot := self.profile.is_bot()) != "":
    #         metadata_content = metadata_content.set_custom_field(
    #             key="bot", value=JsonValue.BOOL(bot)
    #         )

    #     event_builder = EventBuilder.metadata(metadata_content)

    #     event_builder = event_builder.tags(
    #         [
    #             Tag.custom(
    #                 TagKind.SINGLE_LETTER(SingleLetterTag.uppercase(Alphabet.L)),
    #                 [self.profile.get_namespace()],
    #             ),
    #             Tag.custom(
    #                 TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L)),
    #                 [
    #                     self.profile.get_profile_type(),
    #                     self.profile.get_namespace(),
    #                 ],
    #             ),
    #         ]
    #     )

    #     event_builder = event_builder.tags(
    #         [Tag.hashtag(hashtag) for hashtag in self.profile.get_hashtags()]
    #     )

    #     return await self._async_publish_event(event_builder)

    # async def _async_start_notifications(self) -> None:
    #     """
    #     Start handling notifications in the background.
    #     """
    #     if self.notification_task is None or self.notification_task.done():
    #         self.stop_event.clear()  # Reset stop flag

    #         # Create a separate task for background processing
    #         async def process_background_tasks():
    #             while not self.stop_event.is_set():
    #                 # Process any pending gift-wrapped messages
    #                 if (
    #                     hasattr(self, "private_gift_wrapped_message")
    #                     and self.private_gift_wrapped_message
    #                 ):
    #                     event = self.private_gift_wrapped_message
    #                     self.private_gift_wrapped_message = None
    #                     try:
    #                         unwrapped_gift = await self.client.unwrap_gift_wrap(event)
    #                         unsigned_event = unwrapped_gift.rumor()
    #                         self.private_message = unsigned_event
    #                     except Exception as e:
    #                         self.logger.error("Error unwrapping gift: %s", e)

    #                 await asyncio.sleep(0.1)

    #         # Start the background task first
    #         self.background_task = asyncio.create_task(process_background_tasks())

    #         # Start the notification handler - this might be blocking!
    #         await self.client.handle_notifications(self.MyNotificationHandler(self))

    # async def _async_stop_notifications(self) -> None:
    #     """
    #     Gracefully stop handling notifications, with debug logs.
    #     """
    #     NostrClient.logger.debug("Attempting to stop notifications...")

    #     # Step 1: Set the stop event
    #     self.stop_event.set()
    #     NostrClient.logger.debug("Stop event set. Notifier should stop soon.")

    #     # Step 2: Check if a notification task is running
    #     if self.notification_task is None:
    #         NostrClient.logger.debug("No active notification task. Nothing to stop.")
    #         return

    #     if self.notification_task.done():
    #         NostrClient.logger.debug(
    #             "Notification task already completed. Cleaning up reference."
    #         )
    #         self.notification_task = None
    #         return

    #     # Step 3: Attempt to cancel the notification task
    #     NostrClient.logger.debug("Cancelling notification task...")
    #     self.notification_task.cancel()

    #     try:
    #         await self.notification_task  # Ensure proper cancellation
    #         NostrClient.logger.debug("Notification task successfully stopped.")
    #     except asyncio.CancelledError:
    #         NostrClient.logger.debug("Notification task was forcefully cancelled.")

    #     # Step 4: Clean up
    #     self.notification_task = None
    #     NostrClient.logger.debug("_stop_notifications() completed.")

    # class MyNotificationHandler(HandleNotification):
    #     """
    #     Inner class to handle notifications.
    #     """

    #     def __init__(self, nostr_client: "NostrClient") -> None:
    #         """
    #         Initialize the notification handler.
    #         """
    #         super().__init__()
    #         self.nostr_client: NostrClient = nostr_client

    #     async def _process_gift_wrap_message(self, event: Event) -> None:
    #         """
    #         Helper method to process gift wrap messages asynchronously.
    #         """
    #         try:
    #             unwrapped_gift = await self.nostr_client.client.unwrap_gift_wrap(event)
    #             unsigned_event = unwrapped_gift.rumor()
    #             self.nostr_client.private_message = unsigned_event
    #         except Exception as e:
    #             self.nostr_client.logger.error(f"Error unwrapping gift: {e}")
    #             # Don't re-raise the exception in the background task

    #     async def handle_msg(self, relay_url: str, msg: RelayMessage) -> None:
    #         """
    #         Handle a message from the relay.
    #         This method must be synchronous and must not return any awaitable objects.
    #         """
    #         self.nostr_client.logger.debug("Received message: %s", msg)
    #         if self.nostr_client.stop_event.is_set():
    #             return

    #         msg_enum = msg.as_enum()

    #         if msg_enum.is_end_of_stored_events():
    #             self.nostr_client.received_eose = True
    #             self.nostr_client.logger.debug("Received EOSE")
    #         elif msg_enum.is_event_msg():
    #             # Handle regular event messages
    #             self.nostr_client.logger.debug(
    #                 "Received event: %s", msg_enum.event.content()
    #             )
    #             # Use get_running_loop() instead of get_event_loop()
    #             try:
    #                 self.nostr_client.last_message_time = (
    #                     asyncio.get_running_loop().time()
    #                 )
    #             except RuntimeError:
    #                 # If we're not in an event loop context, just ignore this
    #                 pass

    #             if msg_enum.event.kind() == Kind(4):
    #                 self.nostr_client.logger.debug(
    #                     "Received `kind:4` message: %s", msg_enum.event.content()
    #                 )
    #                 self.nostr_client.direct_message = msg_enum.event

    #             if msg_enum.event.kind() == Kind(1059):
    #                 self.nostr_client.logger.debug(
    #                     "Received `kind:1059` message: %s", msg_enum.event.content()
    #                 )
    #                 # Store the event for later processing - DON'T create async tasks here
    #                 self.nostr_client.private_gift_wrapped_message = msg_enum.event
    #         else:
    #             self.nostr_client.logger.debug(
    #                 f"Received unknown message from {relay_url}: {msg}"
    #             )

    #     async def handle(
    #         self, relay_url: str, subscription_id: str, event: Event
    #     ) -> None:
    #         """
    #         Handle an event from the relay.
    #         """
    #         self.nostr_client.logger.debug("Received event: %s", event)
    #         if self.nostr_client.stop_event.is_set():
    #             return

    #         try:
    #             self.nostr_client.last_message_time = asyncio.get_running_loop().time()
    #         except RuntimeError:
    #             # If we're not in an event loop context, just ignore this
    #             pass
    #         if event.kind() == Kind(4):
    #             self.nostr_client.logger.debug(
    #                 "Received `kind:4` message: %s", event.content()
    #             )
    #             self.nostr_client.direct_message = event
    #         if event.kind() == Kind(1059):
    #             self.nostr_client.logger.debug(
    #                 "Received `kind:1059` message: %s", event.content()
    #             )
    #             # Store the event for later processing - DON'T create async tasks
    #             self.nostr_client.private_gift_wrapped_message = event


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
    keys = Keys.generate()
    nsec = keys.secret_key().to_bech32()

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

    return NostrKeys.from_private_key(nsec)
