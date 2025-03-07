"""
Core Nostr utilities for agentstr.
"""

import asyncio
import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .models import NostrKeys, Product, Profile, Stall

try:
    from nostr_sdk import (
        Alphabet,
        Client,
        Coordinate,
        EventBuilder,
        EventId,
        Events,
        Filter,
        Keys,
        Kind,
        Metadata,
        NostrSigner,
        ProductData,
        PublicKey,
        SingleLetterTag,
        Tag,
        TagKind,
        TagStandard,
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
        try:
            # Download the profile from the relay if it already exists
            self.profile = self.retrieve_profile(self.keys.public_key().to_bech32())
        except RuntimeError:
            # If the profile doesn't exist, create a new one
            self.profile = Profile(self.keys.public_key().to_bech32())

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

    ## TODO: make this function available without using EventBuilder
    # def publish_event(self, event_builder: EventBuilder) -> EventId:
    #     """
    #     Publish generic Nostr event to the relay

    #     Returns:
    #         EventId: event id published

    #     Raises:
    #         RuntimeError: if the product can't be published
    #     """
    #     # Run the async publishing function synchronously
    #     return asyncio.run(self._async_publish_event(event_builder))

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
        event_id_obj = asyncio.run(self._async_publish_note(text))
        return event_id_obj.to_bech32()

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
        except Exception as e:
            raise RuntimeError(f"Failed to publish product: {e}") from e

    def publish_profile(self) -> str:
        """
        Publish the Nostr client profile

        Returns:
            str: id of the event publishing the profile

        Raises:
            RuntimeError: if the profile can't be published
        """
        # Run the async publishing function synchronously
        try:
            event_id_obj = asyncio.run(self._async_publish_profile())
            return event_id_obj.to_bech32()
        except Exception as e:
            raise RuntimeError(f"Failed to publish profile: {e}") from e

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
        except Exception as e:
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

    def retrieve_merchants(self) -> set[Profile]:
        """
        Retrieve all merchants from the relay.
        Merchants are npubs who have published a stall.
        Return set may be empty if metadata can't be retrieved for any author.

        Returns:
            set[Profile]: set of merchant profiles
            (skips authors with missing metadata)
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
                    except RuntimeError:
                        continue

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
                    categories=content.get("categories", []),
                )
                products.append(Product.from_product_data(product_data))
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
            RuntimeError: if the profile can't be retrieved
        """

        # Convert public_key to PublicKey
        try:
            public_key_obj = PublicKey.parse(public_key)
        except Exception as e:
            raise RuntimeError(f"Invalid public key: {e}") from e

        try:
            return asyncio.run(self._async_retrieve_profile(public_key_obj))
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve profile: {e}") from e

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

    @classmethod
    def set_logging_level(cls, logging_level: int) -> None:
        """Set the logging level for the NostrClient logger.

        Args:
            logging_level: The logging level (e.g., logging.DEBUG, logging.INFO)
        """
        cls.logger.setLevel(logging_level)
        for handler in cls.logger.handlers:
            handler.setLevel(logging_level)
        cls.logger.info("Logging level set to %s", logging.getLevelName(logging_level))

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

    async def _async_publish_event(self, event_builder: EventBuilder) -> EventId:
        """
        Publish generic Nostr event to the relay

        Returns:
            EventId: event id of the published event

        Raises:
            RuntimeError: if the event can't be published
        """
        try:
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

        # create an event from bad_event_builder to extract the content -
        # not broadcasted
        bad_event = await self.client.sign_event_builder(bad_event_builder)
        content = bad_event.content()

        # build a new event with the right tags and the content
        good_event_builder = EventBuilder(Kind(30018), content).tags(
            [Tag.identifier(product.id), Tag.coordinate(coordinate_tag)]
        )
        NostrClient.logger.info("Product event: %s", good_event_builder)
        return await self._async_publish_event(good_event_builder)

    async def _async_publish_profile(self) -> EventId:
        """
        Asynchronous function to publish a Nostr profile with event kind 0

        Returns:
            EventId: event id if successful

        Raises:
            RuntimeError: if the profile can't be published
        """
        metadata_content = Metadata().set_name(self.profile.get_name())
        metadata_content = metadata_content.set_about(self.profile.get_about())
        metadata_content = metadata_content.set_banner(self.profile.get_banner())
        metadata_content = metadata_content.set_picture(self.profile.get_picture())
        metadata_content = metadata_content.set_website(self.profile.get_website())
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
            await self._async_connect()
        except Exception as e:
            raise RuntimeError("Unable to connect to the relay") from e

        try:
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
        """
        try:
            await self._async_connect()
        except Exception as e:
            raise RuntimeError("Unable to connect to the relay") from e

        try:
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
            seller: PublicKey of the merchant

        Returns:
            Events: list of events containing the products of the seller

        Raises:
            RuntimeError: if the products can't be retrieved
        """
        try:
            await self._async_connect()
        except Exception as e:
            raise RuntimeError("Unable to connect to the relay") from e

        try:
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
            RuntimeError: if the profile can't be retrieved
        """
        try:
            await self._async_connect()
        except Exception as e:
            raise RuntimeError("Unable to connect to the relay") from e

        try:
            metadata = await self.client.fetch_metadata(
                public_key=public_key, timeout=timedelta(seconds=2)
            )
            return Profile.from_metadata(metadata, public_key.to_bech32())
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve metadata: {e}") from e

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
            await self._async_connect()
        except Exception as e:
            raise RuntimeError("Unable to connect to the relay") from e

        try:
            events_filter = Filter().kind(Kind(30017)).authors([merchant])
            events = await self.client.fetch_events_from(
                urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
            )
            return events
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve stalls: {e}") from e


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
