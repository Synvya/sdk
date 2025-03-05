"""
Core Nostr utilities for agentstr.
"""

import asyncio
import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional

from agentstr.models import MerchantProduct, MerchantStall, NostrProfile

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
        StallData,
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

    def __init__(
        self,
        relay: str,
        nsec: str,
    ) -> None:
        """
        Initialize the Nostr client.

        Args:
            relay: Nostr relay that the client will connect to
            nsec: Nostr private key in bech32 format
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
        self.keys = Keys.parse(nsec)
        self.nostr_signer = NostrSigner.keys(self.keys)
        self.client = Client(self.nostr_signer)
        self.connected = False

    def delete_event(self, event_id: EventId, reason: Optional[str] = None) -> EventId:
        """
        Requests the relay to delete an event. Relays may or may not honor the request.

        Args:
            event_id: EventId associated with the event to be deleted
            reason: optional reason for deleting the event

        Returns:
            EventId: if of the event requesting the deletion of event_id

        Raises:
            RuntimeError: if the deletion event can't be published
        """
        event_builder = EventBuilder.delete(ids=[event_id], reason=reason)
        # Run the async publishing function synchronously
        return asyncio.run(self._async_publish_event(event_builder))

    def publish_event(self, event_builder: EventBuilder) -> EventId:
        """
        Publish generic Nostr event to the relay

        Returns:
            EventId: event id published

        Raises:
            RuntimeError: if the product can't be published
        """
        # Run the async publishing function synchronously
        return asyncio.run(self._async_publish_event(event_builder))

    def publish_note(self, text: str) -> EventId:
        """Publish note with event kind 1

        Args:
            text: text to be published as kind 1 event

        Returns:
            EventId: EventId if successful

        Raises:
            RuntimeError: if the product can't be published
        """
        # Run the async publishing function synchronously
        return asyncio.run(self._async_publish_note(text))

    def publish_product(self, product: MerchantProduct) -> EventId:
        """
        Create or update a NIP-15 Marketplace product with event kind 30018

        Args:
            product: product to be published

        Returns:
            EventId: event id of the publication event

        Raises:
            RuntimeError: if the product can't be published
        """
        # Run the async publishing function synchronously
        try:
            return asyncio.run(self._async_publish_product(product))
        except Exception as e:
            raise RuntimeError(f"Failed to publish product: {e}") from e

    def publish_profile(
        self,
        name: str,
        about: str,
        picture: str,
        banner: str,
        website: Optional[str] = None,
    ) -> EventId:
        """
        Publish a Nostr profile with event kind 0

        Args:
            name: name of the Nostr profile
            about: brief description about the profile
            picture: url to a file with a picture for the profile
            banner: url to a file with a banner for the profile
            website: optional url to a website for the profile

        Returns:
            EventId: event id if successful

        Raises:
            RuntimeError: if the profile can't be published
        """
        # Run the async publishing function synchronously
        return asyncio.run(
            self._async_publish_profile(name, about, picture, banner, website)
        )

    def publish_stall(self, stall: MerchantStall) -> EventId:
        """Publish a stall to nostr

        Args:
            stall: stall to be published

        Returns:
            EventId: Id of the publication event

        Raises:
            RuntimeError: if the stall can't be published
        """
        try:
            return asyncio.run(self._async_publish_stall(stall))
        except Exception as e:
            raise RuntimeError(f"Failed to publish stall: {e}") from e

    def retrieve_marketplace(self, owner: PublicKey, name: str) -> set[NostrProfile]:
        """
        Retrieve all sellers from the marketplace.

        Args:
            owner: PublicKey of the owner of the marketplace
            name: name of the marketplace

        Returns:
            set[NostrProfile]: set of seller profiles.
            (skips authors with missing metadata)
        """
        events_filter = Filter().kind(Kind(30019)).authors([owner])
        try:
            events = asyncio.run(self._async_retrieve_events(events_filter))
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve marketplace: {e}") from e

        events_list = events.to_vec()
        merchants_dict: Dict[PublicKey, NostrProfile] = {}

        for event in events_list:
            content = json.loads(event.content())
            if content.get("name") == name:
                merchants = content.get("merchants", [])
                for merchant in merchants:
                    try:
                        public_key = PublicKey.parse(merchant)
                        profile = asyncio.run(self._async_retrieve_profile(public_key))
                        merchants_dict[public_key] = profile
                    except RuntimeError:
                        continue

        return set(merchants_dict.values())

    def retrieve_products_from_seller(self, seller: PublicKey) -> List[MerchantProduct]:
        """
        Retrieve all products from a given seller.

        Args:
            seller: PublicKey of the seller

        Returns:
            List[MerchantProduct]: list of products from the seller
        """
        products = []
        try:
            events = asyncio.run(self._async_retrieve_products_from_seller(seller))
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
                products.append(MerchantProduct.from_product_data(product_data))
            return products
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve products: {e}") from e

    def retrieve_profile(self, public_key: PublicKey) -> NostrProfile:
        """
        Retrieve a Nostr profile from the relay.

        Args:
            public_key: bech32 encoded public key of the profile to retrieve

        Returns:
            NostrProfile: profile of the author

        Raises:
            RuntimeError: if the profile can't be retrieved
        """
        try:
            return asyncio.run(self._async_retrieve_profile(public_key))
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve profile: {e}") from e

    def retrieve_sellers(self) -> set[NostrProfile]:
        """
        Retrieve all sellers from the relay.
        Sellers are npubs who have published a stall.
        Return set may be empty if metadata can't be retrieved for any author.

        Returns:
            set[NostrProfile]: set of seller profiles
            (skips authors with missing metadata)
        """

        # sellers: set[NostrProfile] = set()

        # First we retrieve all stalls from the relay

        try:
            events = asyncio.run(self._async_retrieve_all_stalls())
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve stalls: {e}") from e

        # Now we search for unique npubs from the list of stalls

        events_list = events.to_vec()
        authors: Dict[PublicKey, NostrProfile] = {}

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

    def retrieve_stalls_from_seller(self, seller: PublicKey) -> List[StallData]:
        """
        Retrieve all stalls from a given seller.

        Args:
            seller: PublicKey of the seller

        Returns:
            List[StallData]: list of stalls from the seller

        Raises:
            RuntimeError: if the stalls can't be retrieved
        """
        stalls = []
        try:
            events = asyncio.run(self._async_retrieve_stalls_from_seller(seller))
            events_list = events.to_vec()
            for event in events_list:
                try:
                    # Parse the content field instead of the whole event
                    content = event.content()
                    stall = StallData.from_json(content)
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

            # Add debug logging
            NostrClient.logger.debug("Attempting to publish event: %s", event_builder)
            NostrClient.logger.debug(
                "Using keys: %s", self.keys.public_key().to_bech32()
            )

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

    async def _async_publish_product(self, product: MerchantProduct) -> EventId:
        """
        Asynchronous function to create or update a NIP-15
        Marketplace product with event kind 30018

        Args:
            product: product to publish

        Returns:
            EventId: event id if successful

        Raises:
            RuntimeError: if the product can't be published
        """
        coordinate_tag = Coordinate(
            Kind(30017), self.keys.public_key(), product.stall_id
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

    async def _async_publish_profile(
        self,
        name: str,
        about: str,
        picture: str,
        banner: str,
        website: Optional[str] = None,
    ) -> EventId:
        """
        Asynchronous function to publish a Nostr profile with event kind 0

        Args:
            name: name of the Nostr profile
            about: brief description about the profile
            picture: url to a file with a picture for the profile
            banner: url to a file with a banner for the profile
            website: optional url to a website for the profile

        Returns:
            EventId: event id if successful

        Raises:
            RuntimeError: if the profile can't be published
        """
        metadata_content = Metadata().set_name(name)
        metadata_content = metadata_content.set_about(about)
        metadata_content = metadata_content.set_banner(banner)
        metadata_content = metadata_content.set_picture(picture)

        if website:
            metadata_content = metadata_content.set_website(website)

        event_builder = EventBuilder.metadata(metadata_content)
        return await self._async_publish_event(event_builder)

    async def _async_publish_stall(self, stall: MerchantStall) -> EventId:
        """
        Asynchronous function to create or update a NIP-15
        Marketplace stall with event kind 30017

        Args:
            stall: stall to be published

        Returns:
            EventId: Id of the publication event

        Raises:
            RuntimeError: if the profile can't be published
        """

        # good_event_builder = EventBuilder(Kind(30018), content).tags(
        #     [Tag.identifier(product.id), Tag.coordinate(coordinate_tag)]
        # )

        NostrClient.logger.info("Merchant Stall: %s", stall)
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

    async def _async_retrieve_products_from_seller(self, seller: PublicKey) -> Events:
        """
        Asynchronous function to retrieve the products for a given author

        Args:
            seller: PublicKey of the seller to retrieve the products for

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
            events_filter = Filter().kind(Kind(30018)).authors([seller])
            events = await self.client.fetch_events_from(
                urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
            )
            return events
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve stalls: {e}") from e

    async def _async_retrieve_profile(self, author: PublicKey) -> NostrProfile:
        """
        Asynchronous function to retrieve the profile for a given author

        Args:
            author: PublicKey of the author to retrieve the profile for

        Returns:
            NostrProfile: profile of the author

        Raises:
            RuntimeError: if the profile can't be retrieved
        """
        try:
            await self._async_connect()
        except Exception as e:
            raise RuntimeError("Unable to connect to the relay") from e

        try:
            metadata = await self.client.fetch_metadata(
                public_key=author, timeout=timedelta(seconds=2)
            )
            return NostrProfile.from_metadata(metadata, author)
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve metadata: {e}") from e

    async def _async_retrieve_stalls_from_seller(self, seller: PublicKey) -> Events:
        """
        Asynchronous function to retrieve the stall for a given author

        Args:
            seller: PublicKey of the seller to retrieve the stall for

        Returns:
            Events: list of events containing the stalls of the seller

        Raises:
            RuntimeError: if the stall can't be retrieved
        """
        try:
            await self._async_connect()
        except Exception as e:
            raise RuntimeError("Unable to connect to the relay") from e

        try:
            events_filter = Filter().kind(Kind(30017)).authors([seller])
            events = await self.client.fetch_events_from(
                urls=[self.relay], filter=events_filter, timeout=timedelta(seconds=2)
            )
            return events
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve stalls: {e}") from e


def generate_and_save_keys(env_var: str, env_path: Path) -> Keys:
    """Generate new nostr keys and save the private key to .env file.

    Args:
        env_var: Name of the environment variable to store the key
        env_path: Path to the .env file. If None, looks for .env in current directory

    Returns:
        The generated Keys object
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

    return keys
