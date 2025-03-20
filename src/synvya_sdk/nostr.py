"""
Core Nostr utilities for agentstr.
"""

import asyncio
import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from .models import NostrKeys, Product, Profile, Stall

try:
    from nostr_sdk import (
        Alphabet,
        Client,
        Coordinate,
        Event,
        EventBuilder,
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
        TagStandard,
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

    Nostr is an asynchronous communication protocol. To hide this,
    NostrClient exposes synchronous functions. Users of the NostrClient
    should ignore `_async_` functions which are for internal purposes only.
    """

    logger = logging.getLogger("NostrClient")

    def __init__(self, relay: str, private_key: str) -> None:
        """
        Initialize the Nostr client.

        Args:
            relay: Nostr relay that the client will connect to
            private_key: Private key for the client in hex or bech32 format
        """
        # Set log handling
        if not NostrClient.logger.hasHandlers():
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            NostrClient.logger.addHandler(console_handler)

        # configure relay and keys for the client
        self.relay = relay
        self.keys = Keys.parse(private_key)
        self.nostr_signer = NostrSigner.keys(self.keys)
        self.client = Client(self.nostr_signer)
        self.connected = False
        self.stop_event = asyncio.Event()  # Used to signal stopping
        self.notification_task = None  # To track the background notification task
        self.received_eose = False  # To track if EOSE has been received
        self.private_message: UnsignedEvent = None
        self.direct_message: Event = None

        try:
            self.last_message_time = asyncio.get_running_loop().time()
        except RuntimeError:  # No running loop in sync code, so use default
            self.last_message_time = 0  # Initialize with 0 if no loop is running yet

        try:
            # Download the profile from the relay if it already exists
            self.profile = self.retrieve_profile(self.keys.public_key().to_bech32())
        except ValueError:
            # If the profile doesn't exist, create a new one
            self.profile = Profile(self.keys.public_key().to_bech32())
        except RuntimeError as e:
            raise RuntimeError(f"Unable to connect to relay: {e}") from e

    def delete_event(self, event_id: str, reason: Optional[str] = None) -> str:
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

        event_builder = EventBuilder.delete(ids=[event_id_obj], reason=reason)
        # Run the async publishing function synchronously
        return_event_id_obj = asyncio.run(self._async_publish_event(event_builder))
        return return_event_id_obj.to_bech32()

    def listen_for_messages(self) -> str:
        """Listen for direct messages and private messages from the relay

        Returns:
            str: The response from listening

        Raises:
            RuntimeError: if encountering an error while listening
        """
        try:
            response = asyncio.run(self._async_listen_for_messages())
            NostrClient.logger.debug("Message received: %s", response)
            return response
        except RuntimeError as e:
            raise RuntimeError(f"Failed to listen for messages: {e}") from e

    def publish_event(self, kind: int, content: str) -> str:
        """Publish a generic Nostr event to the relay

        Args:
            kind: kind of the event
            content: content of the event
            tags: tags of the event

        Returns:
            str: id of the event published

        Raises:
            RuntimeError: if the event can't be published
        """
        raise NotImplementedError("This function is not implemented yet")

    def get_profile(self) -> Profile:
        """Get the Nostr profile of the client

        Returns:
            Profile: Nostr profile of the client
        """
        return self.profile

    def publish_note(self, text: str) -> str:
        """Publish note with event kind 1

        Args:
            text: text to be published as kind 1 event

        Returns:
            str: id of the event publishing the note

        Raises:
            RuntimeError: if the note can't be published
        """
        # Run the async publishing function synchronously
        try:
            event_id_obj = asyncio.run(self._async_publish_note(text))
            return event_id_obj.to_bech32()
        except RuntimeError as e:
            raise RuntimeError(f"Failed to publish note: {e}") from e

    def publish_product(self, product: Product) -> str:
        """
        Create or update a NIP-15 Marketplace product with event kind 30018

        Args:
            product: Product to be published

        Returns:
            str: id of the event publishing the product

        Raises:
            RuntimeError: if the product can't be published
        """
        # Run the async publishing function synchronously
        try:
            event_id_obj = asyncio.run(self._async_publish_product(product))
            return event_id_obj.to_bech32()
        except RuntimeError as e:
            raise RuntimeError(f"Failed to publish product: {e}") from e

    def publish_stall(self, stall: Stall) -> str:
        """Publish a stall to nostr

        Args:
            stall: Stall to be published

        Returns:
            str: id of the event publishing the stall

        Raises:
            RuntimeError: if the stall can't be published
        """
        try:
            event_id_obj = asyncio.run(self._async_publish_stall(stall))
            return event_id_obj.to_bech32()
        except RuntimeError as e:
            raise RuntimeError(f"Failed to publish stall: {e}") from e

    def retrieve_marketplace_merchants(
        self, owner: str, marketplace_name: str
    ) -> set[Profile]:
        """
        Retrieve all merchants associated with a given marketplace.

        Args:
            owner: Nostr public key of the marketplace owner in bech32 or hex format
            marketplace_name: name of the marketplace

        Returns:
            set[Profile]: set of merchant profiles.
            (skips authors with missing metadata)

        Raises:
            RuntimeError: if the owner key is invalid
            RuntimeError: if the marketplace can't be retrieved
        """

        # Convert owner to PublicKey
        try:
            owner_key = PublicKey.parse(owner)
        except Exception as e:
            raise RuntimeError(f"Invalid owner key: {e}") from e

        events_filter = Filter().kind(Kind(30019)).authors([owner_key])
        try:
            events = asyncio.run(self._async_retrieve_events(events_filter))
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
                        public_key = PublicKey.parse(merchant)
                        profile = asyncio.run(self._async_retrieve_profile(public_key))
                        merchants_dict[public_key] = profile
                    except RuntimeError:
                        continue

        return set(merchants_dict.values())

    def retrieve_all_merchants(self) -> set[Profile]:
        """
        Retrieve all merchants from the relay.
        Merchants are npubs who have published a stall.
        Return set may be empty if metadata can't be retrieved for any author.

        Returns:
            set[Profile]: set of merchant profiles
            (skips authors with missing metadata)

        Raises:
            RuntimeError: if it can't connect to the relay
        """

        # First we retrieve all stalls from the relay

        try:
            events = asyncio.run(self._async_retrieve_all_stalls())
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve stalls: {e}") from e

        # Now we search for unique npubs from the list of stalls

        events_list = events.to_vec()
        authors: Dict[PublicKey, Profile] = {}

        for event in events_list:
            if event.kind() == Kind(30017):
                # Is this event the first time we see this author?
                if event.author() not in authors:
                    # First time we see this author.
                    # Let's add the profile to the dictionary
                    try:
                        profile = asyncio.run(
                            self._async_retrieve_profile(event.author())
                        )
                        # Add profile to the dictionary
                        # associated with the author's PublicKey
                        authors[event.author()] = profile
                    except ValueError:
                        continue
                    except RuntimeError as e:
                        raise e

                # Now we add locations from the event locations to the profile

                for tag in event.tags().to_vec():
                    standardized_tag = tag.as_standardized()
                    if isinstance(standardized_tag, TagStandard.GEOHASH):
                        string_repr = str(standardized_tag)
                        extracted_geohash = string_repr.split("=")[1].rstrip(
                            ")"
                        )  # Splitting and removing the closing parenthesis

                        profile = authors[event.author()]
                        profile.add_location(extracted_geohash)
                        authors[event.author()] = profile
                    # else:
                    #     print(f"Unknown tag: {standardized_tag}")

        # once we're done iterating over the events, we return the set of profiles
        return set(authors.values())

    def retrieve_products_from_merchant(self, merchant: str) -> List[Product]:
        """
        Retrieve all products from a given merchant.

        Args:
            merchant: Nostr public key of the merchant in bech32 or hex format

        Returns:
            List[Product]: list of products from the merchant

        Raises:
            RuntimeError: if the merchant key is invalid
            RuntimeError: if the products can't be retrieved
        """
        products = []

        # Convert owner to PublicKey
        try:
            merchant_key = PublicKey.parse(merchant)
        except Exception as e:
            raise RuntimeError(f"Invalid merchant key: {e}") from e

        try:
            events = asyncio.run(
                self._async_retrieve_products_from_merchant(merchant_key)
            )
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
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve products: {e}") from e

    def retrieve_profile(self, public_key: str) -> Profile:
        """
        Retrieve a Nostr profile from the relay.

        Args:
            public_key: public key of the profile to retrieve in bech32 or hex format

        Returns:
            Profile: profile of the author

        Raises:
            ValueError: if the public key is invalid
            RuntimeError: if it can't connect to the relay
        """

        # Convert public_key to PublicKey
        try:
            public_key_obj = PublicKey.parse(public_key)
        except Exception as e:
            raise ValueError(f"Invalid public key: {e}") from e

        try:
            return asyncio.run(self._async_retrieve_profile(public_key_obj))
        except RuntimeError as e:
            raise e
        except ValueError as e:
            raise e

    def retrieve_stalls_from_merchant(self, merchant: str) -> List[Stall]:
        """
        Retrieve all stalls from a given merchant.

        Args:
            merchant: Nostr public key of the merchant in bech32 or hex format

        Returns:
            List[Stall]: list of stalls from the merchant

        Raises:
            RuntimeError: if the stalls can't be retrieved
        """
        stalls = []

        # Convert merchant to PublicKey
        try:
            merchant_key = PublicKey.parse(merchant)
        except Exception as e:
            raise RuntimeError(f"Invalid merchant key: {e}") from e

        try:
            events = asyncio.run(
                self._async_retrieve_stalls_from_merchant(merchant_key)
            )
            events_list = events.to_vec()
            for event in events_list:
                try:
                    # Parse the content field instead of the whole event
                    content = event.content()
                    # stall = MerchantStall.from_stall_data(StallData.from_json(content))
                    stall = Stall.from_json(content)
                    stalls.append(stall)
                except RuntimeError as e:
                    self.logger.warning("Failed to parse stall data: %s", e)
                    continue
            return stalls
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve stalls: {e}") from e

    def send_private_message(self, public_key: str, message: str) -> str:
        """
        Send a private message to a given Nostr public key.

        Args:
            public_key: public key of the recipient in bech32 or hex format
            message: message to send

        Returns:
            str: id of the event publishing the message

        Raises:
            RuntimeError: if the message can't be sent
        """
        try:
            event_id_obj = asyncio.run(
                self._async_send_private_message(PublicKey.parse(public_key), message)
            )
            return event_id_obj.to_bech32()
        except Exception as e:
            raise RuntimeError(f"Failed to send private message: {e}") from e

    def set_profile(self, profile: Profile) -> str:
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
        try:
            event_id_obj = asyncio.run(self._async_publish_profile())
            return event_id_obj.to_bech32()
        except RuntimeError as e:
            raise RuntimeError(f"Failed to publish profile: {e}") from e

    async def stop_notifications(self) -> None:
        """
        Gracefully stop handling notifications, with debug logs.
        """
        NostrClient.logger.debug("Attempting to stop notifications...")

        # Step 1: Set the stop event
        self.stop_event.set()
        NostrClient.logger.debug("Stop event set. Notifier should stop soon.")

        # Step 2: Check if a notification task is running
        if self.notification_task is None:
            NostrClient.logger.debug("No active notification task. Nothing to stop.")
            return

        if self.notification_task.done():
            NostrClient.logger.debug(
                "Notification task already completed. Cleaning up reference."
            )
            self.notification_task = None
            return

        # Step 3: Attempt to cancel the notification task
        NostrClient.logger.debug("Cancelling notification task...")
        self.notification_task.cancel()

        try:
            await self.notification_task  # Ensure proper cancellation
            NostrClient.logger.debug("Notification task successfully stopped.")
        except asyncio.CancelledError:
            NostrClient.logger.debug("Notification task was forcefully cancelled.")

        # Step 4: Clean up
        self.notification_task = None
        NostrClient.logger.debug("_stop_notifications() completed.")

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

    async def _async_listen_for_messages(self) -> str:
        """
        Listen for private messages from the relay

        Returns:
            str: content of the private message or an error message

        Raises:
            RuntimeError: if it can't connect to the relay
            RuntimeError: if it can't subscribe to private messages
            RuntimeError: if it can't receive a message
        """

        NostrClient.logger.debug("Listening for private messages.")

        if not self.connected:
            try:
                await self._async_connect()
                NostrClient.logger.debug("Connected to relay %s.", self.relay)
            except Exception as e:
                NostrClient.logger.error("Connection failed: %s", e)
                raise RuntimeError(
                    f"Unable to connect to relay {self.relay}. Exception: {e}."
                ) from e

        try:
            messages_filter = (
                Filter()
                .kinds([Kind(1059), Kind(4)])
                .pubkey(self.keys.public_key())
                .limit(0)
            )

            subscription = await self.client.subscribe(messages_filter, None)
            NostrClient.logger.debug("Subscribed to private messages: %s", subscription)

            if not hasattr(subscription, "success") or not subscription.success:
                raise RuntimeError("Failed to subscribe to private messages")

            self.received_eose = False  # Reset the EOSE flag before listening
            self.last_message_time = (
                asyncio.get_event_loop().time()
            )  # Track the last received message time

            # Start handling notifications in the background
            await self._start_notifications()

            response = "No messages received"

            # Wait for new messages while checking periodically if we should stop
            timeout_seconds = 15  # Adjust this timeout as needed
            while not self.stop_event.is_set():
                await asyncio.sleep(5)  #  Check every 5 seconds

                if self.received_eose:
                    NostrClient.logger.debug("Received EOSE")
                    time_since_last_msg = (
                        asyncio.get_event_loop().time() - self.last_message_time
                    )

                    if time_since_last_msg > timeout_seconds:
                        response = (
                            f"No messages received after {timeout_seconds} seconds"
                        )
                        break  # Stop listening after timeout

                if self.private_message and self.private_message.kind() == Kind(14):
                    response = self.private_message.content()
                    self.private_message = None
                    break
                if self.private_message and self.private_message.kind() == Kind(15):
                    response = self.private_message.content()
                    # TODO: process tags with file type
                    self.private_message = None
                    break
                if self.direct_message:
                    try:
                        response = await self.nostr_signer.nip04_decrypt(
                            self.direct_message.author(), self.direct_message.content()
                        )
                    except Exception as e:
                        raise RuntimeError(
                            f"Unable to decrypt direct message: {e}"
                        ) from e
                    self.direct_message = None
                    break
                NostrClient.logger.debug("Not received private message: %s", response)
        except Exception as e:
            raise RuntimeError(
                f"Unable to listen for private messages. Exception: {e}."
            ) from e
        finally:
            await self.stop_notifications()

        return response

    async def _async_publish_event(self, event_builder: EventBuilder) -> EventId:
        """
        Publish generic Nostr event to the relay

        Returns:
            EventId: event id of the published event

        Raises:
            RuntimeError: if the event can't be published
        """
        try:
            if not self.connected:
                await self._async_connect()

            # Wait for connection and try to publish
            output = await self.client.send_event_builder(event_builder)

            # More detailed error handling
            if not output:
                raise RuntimeError("No output received from send_event_builder")
            if len(output.success) == 0:
                reason = getattr(output, "message", "unknown")
                raise RuntimeError(f"Event rejected by relay. Reason: {reason}")

            NostrClient.logger.info(
                "Event published with event id: %s", output.id.to_bech32()
            )
            return output.id

        except Exception as e:
            NostrClient.logger.error("Failed to publish event: %s", str(e))
            NostrClient.logger.debug("Event details:", exc_info=True)
            raise RuntimeError(f"Unable to publish event: {str(e)}") from e

    async def _async_publish_note(self, text: str) -> EventId:
        """
        Asynchronous funcion to publish kind 1 event (text note) to the relay

        Args:
            text: text to be published as kind 1 event

        Returns:
            EventId: event id if successful

        Raises:
            RuntimeError: if the event can't be published
        """
        event_builder = EventBuilder.text_note(text)
        return await self._async_publish_event(event_builder)

    async def _async_publish_product(self, product: Product) -> EventId:
        """
        Asynchronous function to create or update a NIP-15
        Marketplace product with event kind 30018

        Args:
            product: Product to publish

        Returns:
            EventId: event id if successful

        Raises:
            RuntimeError: if the product can't be published
        """
        coordinate_tag = Coordinate(
            Kind(30017),
            PublicKey.parse(self.profile.get_public_key()),
            product.stall_id,
        )

        # EventBuilder.product_data() has a bug with tag handling.
        # We use the function to create the content field and discard the eventbuilder
        bad_event_builder = EventBuilder.product_data(product.to_product_data())
        NostrClient.logger.info("Bad event builder: %s", bad_event_builder)

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

        NostrClient.logger.info("Good event builder: %s", good_event_builder)
        return await self._async_publish_event(good_event_builder)

    async def _async_publish_profile(self) -> EventId:
        """
        Asynchronous function to publish a Nostr profile with event kind 0

        Returns:
            EventId: event id if successful

        Raises:
            RuntimeError: if the profile can't be published
        """

        metadata_content = Metadata().set_about(self.profile.get_about())
        metadata_content = metadata_content.set_banner(self.profile.get_banner())
        metadata_content = metadata_content.set_display_name(
            self.profile.get_display_name()
        )
        metadata_content = metadata_content.set_name(self.profile.get_name())
        metadata_content = metadata_content.set_nip05(self.profile.get_nip05())
        metadata_content = metadata_content.set_picture(self.profile.get_picture())
        metadata_content = metadata_content.set_website(self.profile.get_website())
        metadata_content = metadata_content.set_custom_field(
            key="bot", value=JsonValue.BOOL(self.profile.is_bot())
        )
        event_builder = EventBuilder.metadata(metadata_content)
        return await self._async_publish_event(event_builder)

    async def _async_publish_stall(self, stall: Stall) -> EventId:
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

        # good_event_builder = EventBuilder(Kind(30018), content).tags(
        #     [Tag.identifier(product.id), Tag.coordinate(coordinate_tag)]
        # )

        NostrClient.logger.info("Stall: %s", stall)
        event_builder = EventBuilder.stall_data(stall.to_stall_data()).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.G)),
                    [stall.geohash],
                ),
            ]
        )
        return await self._async_publish_event(event_builder)

    async def _async_retrieve_all_stalls(self) -> Events:
        """
        Asynchronous function to retreive all stalls from a relay
        This function is used internally to find Merchants.

        Returns:
            Events: events containing all stalls.

        Raises:
            RuntimeError: if the stalls can't be retrieved
        """
        try:
            if not self.connected:
                await self._async_connect()

            events_filter = Filter().kind(Kind(30017))
            events = await self.client.fetch_events_from(
                urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
            )
            return events
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve stalls: {e}") from e

    async def _async_retrieve_events(self, events_filter: Filter) -> Events:
        """
        Asynchronous function to retrieve events from the relay

        Args:
            events_filter: Filter to apply to the events

        Returns:
            Events: list of events

        Raises:
            RuntimeError: if the events can't be retrieved
        """
        try:
            if not self.connected:
                await self._async_connect()

            events = await self.client.fetch_events_from(
                urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
            )
            return events
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve stalls: {e}") from e

    async def _async_retrieve_products_from_merchant(
        self, merchant: PublicKey
    ) -> Events:
        """
        Asynchronous function to retrieve the products for a given merchant

        Args:
            merchant: PublicKey of the merchant

        Returns:
            Events: list of events containing the products of the merchant

        Raises:
            RuntimeError: if the products can't be retrieved
        """
        try:
            if not self.connected:
                await self._async_connect()

            # print(f"Retrieving products from seller: {seller}")
            events_filter = Filter().kind(Kind(30018)).authors([merchant])
            events = await self.client.fetch_events_from(
                urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
            )
            return events
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve stalls: {e}") from e

    async def _async_retrieve_profile(self, public_key: PublicKey) -> Profile:
        """
        Asynchronous function to retrieve the profile for a given author

        Args:
            public_key: public key of the profile to retrieve

        Returns:
            Profile: profile associated with the public key

        Raises:
            RuntimeError: if it can't connect to the relay
            ValueError: if a profile is not found
        """
        try:
            if not self.connected:
                await self._async_connect()

            metadata = await self.client.fetch_metadata(
                public_key=public_key, timeout=timedelta(seconds=2)
            )
            profile = await Profile.from_metadata(metadata, public_key.to_bech32())
            return profile
        except RuntimeError as e:
            raise RuntimeError(f"Unable to connect to relay: {e}") from e
        except Exception as e:
            raise ValueError(f"Unable to retrieve metadata: {e}") from e

    async def _async_retrieve_stalls_from_merchant(self, merchant: PublicKey) -> Events:
        """
        Asynchronous function to retrieve the stall for a given merchant

        Args:
            seller: PublicKey of the merchant to retrieve the stall for

        Returns:
            Events: list of events containing the stalls of the merchant

        Raises:
            RuntimeError: if the stall can't be retrieved
        """
        try:
            if not self.connected:
                await self._async_connect()

            events_filter = Filter().kind(Kind(30017)).authors([merchant])
            events = await self.client.fetch_events_from(
                urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
            )
            return events
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve stalls: {e}") from e

    async def _async_send_private_message(
        self, public_key: PublicKey, message: str
    ) -> EventId:
        """
        Asynchronous function to send a private message to a given Nostr public key

        Args:
            public_key: public key of the recipient in bech32 or hex format
            message: message to send

        Returns:
            EventId: event id of the message

        Raises:
            RuntimeError: if the message can't be sent
        """
        try:
            output = await self.client.send_private_msg(public_key, message)
            if len(output.success) > 0:
                NostrClient.logger.info(
                    "Message sent to %s: %s", public_key.to_bech32(), message
                )
                return output.id
            # no relay received the message
            NostrClient.logger.error(
                "Message not sent to %s: %s", public_key.to_bech32(), message
            )
            raise RuntimeError("Unable to send private message:")
        except Exception as e:
            raise RuntimeError(f"Unable to send private message: {e}") from e

    async def _start_notifications(self) -> None:
        """
        Start handling notifications in the background.
        """
        if self.notification_task is None or self.notification_task.done():
            self.stop_event.clear()  # Reset stop flag
            self.notification_task = asyncio.create_task(
                self.client.handle_notifications(self.MyNotificationHandler(self))
            )

    class MyNotificationHandler(HandleNotification):
        """
        Inner class to handle notifications.
        """

        def __init__(self, nostr_client: "NostrClient"):
            self.nostr_client = nostr_client

        async def handle_msg(self, relay_url: str, msg: RelayMessage):
            """
            Handle a message from the relay.
            """
            if self.nostr_client.stop_event.is_set():
                return

            msg_enum = msg.as_enum()

            if msg_enum.is_end_of_stored_events():
                self.nostr_client.received_eose = True
            elif msg_enum.is_event_msg():
                # await self.handle(relay_url, msg_enum.subscription_id, msg_enum.event)

                self.nostr_client.last_message_time = asyncio.get_event_loop().time()

                if msg_enum.event.kind() == Kind(4):
                    self.nostr_client.direct_message = msg_enum.event

                if msg_enum.event.kind() == Kind(1059):

                    try:
                        unwrapped_gift = (
                            await self.nostr_client.client.unwrap_gift_wrap(
                                msg_enum.event
                            )
                        )
                    except Exception as e:
                        self.nostr_client.logger.error(f"Error unwrapping gift: {e}")
                        raise
                    unsigned_event = unwrapped_gift.rumor()
                    # Assign the unsigned event to the NostrClient private message
                    # to be processed in the _async_process_unsigned_event method
                    self.nostr_client.private_message = unsigned_event
            else:
                self.nostr_client.logger.debug(
                    f"Received unknown message from {relay_url}: {msg}"
                )

        async def handle(self, relay_url: str, subscription_id: str, event: Event):
            """
            Handle an event from the relay.
            """
            if self.nostr_client.stop_event.is_set():
                return

            self.nostr_client.last_message_time = asyncio.get_event_loop().time()
            if event.kind() == Kind(4):
                self.nostr_client.direct_message = event
            if event.kind() == Kind(1059):
                try:
                    unwrapped_gift = await self.nostr_client.client.unwrap_gift_wrap(
                        event
                    )
                except Exception as e:
                    self.nostr_client.logger.error(f"Error unwrapping gift: {e}")
                    raise
                unsigned_event = unwrapped_gift.rumor()
                self.nostr_client.logger.debug(
                    f"Received event kind: {unsigned_event.kind()}"
                )
                self.nostr_client.private_message = unsigned_event
                if unsigned_event.kind() == Kind(14):
                    self.nostr_client.logger.debug(
                        f"Received private message: {unsigned_event.content()}"
                    )
                    self.nostr_client.logger.debug(
                        f"From: {unsigned_event.author().to_bech32()}"
                    )


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
