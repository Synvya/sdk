import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import List, Optional

from agentstr.utils import Profile

try:
    import asyncio
except ImportError:
    raise ImportError(
        "`asyncio` not installed. Please install using `pip install asyncio`"
    )

try:
    from nostr_sdk import (
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
        ShippingCost,
        ShippingMethod,
        StallData,
        Tag,
        Timestamp,
    )

except ImportError:
    raise ImportError(
        "`nostr_sdk` not installed. Please install using `pip install nostr_sdk`"
    )


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


class NostrProfile(Profile):
    """
    NostrProfile is a Profile that is used to represent a public Nostr profile.

    Key difference between NostrProfile and AgentProfile is that NostrProfile represents a third party profile and therefore we only have its public key.
    """

    WEB_URL: str = "https://primal.net/p/"
    profile_url: str
    public_key: PublicKey

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

    def get_public_key(self) -> str:
        """Get the public key of the Nostr profile.

        Returns:
            str: bech32 encoded public key of the Nostr profile
        """
        return str(self.public_key.to_bech32())

    def to_json(self) -> str:
        # Parse parent's JSON string back to dict
        data = json.loads(super().to_json())
        # Add NostrProfile-specific fields
        data.update(
            {
                "profile_url": self.profile_url,
                "public_key": self.public_key.to_bech32(),
            }
        )
        return json.dumps(data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NostrProfile):
            return False
        return str(self.public_key.to_bech32()) == str(other.public_key.to_bech32())

    def __hash__(self) -> int:
        return hash(str(self.public_key.to_bech32()))


class NostrClient:
    """
    NostrClient implements the set of Nostr utilities required for higher level functions implementing
    like the Marketplace.

    Nostr is an asynchronous communication protocol. To hide this, NostrClient exposes synchronous functions.
    Users of the NostrClient should ignore `_async_` functions which are for internal purposes only.
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

    def publish_product(self, product: ProductData) -> EventId:
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
        return asyncio.run(self._async_publish_product(product))

    def publish_profile(self, name: str, about: str, picture: str) -> EventId:
        """
        Publish a Nostr profile with event kind 0

        Args:
            name: name of the Nostr profile
            about: brief description about the profile
            picture: url to a png file with a picture for the profile

        Returns:
            EventId: event id if successful

        Raises:
            RuntimeError: if the profile can't be published
        """
        # Run the async publishing function synchronously
        return asyncio.run(self._async_publish_profile(name, about, picture))

    def publish_stall(self, stall: StallData) -> EventId:
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
            raise RuntimeError(f"Failed to publish stall: {e}")

    def retrieve_sellers(self) -> set[NostrProfile]:
        """
        Retrieve all sellers from the relay.
        Sellers are npubs who have published a stall.
        Return set may be empty if metadata can't be retrieved for any author.

        Returns:
            set[NostrProfile]: set of seller profiles (skips authors with missing metadata)
        """
        sellers = set()

        # First we retrieve all stalls from the relay
        try:
            events = asyncio.run(self._async_retrieve_all_stalls())
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve stalls: {e}")

        # Now we search for unique npubs from the list of stalls
        events_list = events.to_vec()
        authors = set()
        for event in events_list:
            if event.kind() == Kind(30017):
                authors.add(event.author())

        # Retrieve the profiles and build the set of merchants
        for author in authors:
            try:
                profile = asyncio.run(self._async_retrieve_profile(author))
                sellers.add(profile)
            except Exception as e:
                # self.logger.info(f"Skipping author - failed to retrieve metadata: {e}")
                continue

        return sellers

    def retrieve_stalls_from_seller(self, public_key: str) -> List[StallData]:
        """
        Retrieve all stalls from a given seller.

        Args:
            public_key: bech32 encoded public key of the seller

        Returns:
            List[StallData]: list of stalls from the seller
        """
        stalls = []
        try:
            events = asyncio.run(
                self._async_retrieve_stalls_from_seller(PublicKey.parse(public_key))
            )
            events_list = events.to_vec()
            for event in events_list:
                try:
                    # Parse the content field instead of the whole event
                    content = event.content()
                    stall = StallData.from_json(content)
                    stalls.append(stall)
                except Exception as e:
                    self.logger.warning(f"Failed to parse stall data: {e}")
                    continue
            return stalls
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve stalls: {e}")

    @classmethod
    def set_logging_level(cls, logging_level: int) -> None:
        """Set the logging level for the NostrClient logger.

        Args:
            logging_level: The logging level (e.g., logging.DEBUG, logging.INFO)
        """
        cls.logger.setLevel(logging_level)
        for handler in cls.logger.handlers:
            handler.setLevel(logging_level)
        cls.logger.info(f"Logging level set to {logging.getLevelName(logging_level)}")

    # ----------------------------------------------------------------------------------------------
    # --*-- async functions for internal use only. Developers should use synchronous functions above
    # ----------------------------------------------------------------------------------------------

    async def _async_connect(self) -> None:
        """Asynchronous function to add relay to the NostrClient instance and connect to it.
        TBD: refactor to not return anything if successful and raise an exception if not

        Raises:
            RuntimeError: if the relay can't be connected to
        """
        try:
            await self.client.add_relay(self.relay)
            NostrClient.logger.info(f"Relay {self.relay} succesfully added.")
            await self.client.connect()
            NostrClient.logger.info("Connected to relay.")
        except Exception as e:
            raise RuntimeError(
                f"Unable to connect to relay {self.relay}. Exception: {e}."
            )

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
        except Exception as e:
            raise RuntimeError(f"Unable to connect to the relay: {e}")

        try:
            output = await self.client.send_event_builder(event_builder)
            if len(output.success) > 0:
                NostrClient.logger.info(
                    f"Event published with event id: {output.id.to_bech32()}"
                )
                return output.id
            else:
                raise RuntimeError("Unable to publish event")
        except Exception as e:
            NostrClient.logger.error(
                f"NostrClient instance not properly initialized. Exception: {e}."
            )
            raise RuntimeError(f"Unable to publish event: {e}.")

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

    async def _async_publish_product(self, product: ProductData) -> EventId:
        """
        Asynchronous function to create or update a NIP-15 Marketplace product with event kind 30018

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
        bad_event_builder = EventBuilder.product_data(product)

        # create an event from bad_event_builder to extract the content - not broadcasted
        bad_event = await self.client.sign_event_builder(bad_event_builder)
        content = bad_event.content()

        # build a new event with the right tags and the content
        good_event_builder = EventBuilder(Kind(30018), content).tags(
            [Tag.identifier(product.id), Tag.coordinate(coordinate_tag)]
        )
        self.logger.info("Product event: " + str(good_event_builder))
        return await self._async_publish_event(good_event_builder)

    async def _async_publish_profile(
        self, name: str, about: str, picture: str
    ) -> EventId:
        """
        Asynchronous function to publish a Nostr profile with event kind 0

        Args:
            name: name of the Nostr profile
            about: brief description about the profile
            picture: url to a png file with a picture for the profile

        Returns:
            EventId: event id if successful

        Raises:
            RuntimeError: if the profile can't be published
        """
        metadata_content = Metadata().set_name(name)
        metadata_content = metadata_content.set_about(about)
        metadata_content = metadata_content.set_picture(picture)

        event_builder = EventBuilder.metadata(metadata_content)
        return await self._async_publish_event(event_builder)

    async def _async_publish_stall(self, stall: StallData) -> EventId:
        """
        Asynchronous function to create or update a NIP-15 Marketplace stall with event kind 30017

        Args:
            stall: stall to be published

        Returns:
            EventId: Id of the publication event

        Raises:
            RuntimeError: if the profile can't be published
        """

        self.logger.info(f"Stall: {stall}")
        event_builder = EventBuilder.stall_data(stall)
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
            raise RuntimeError("Unable to connect to the relay")

        try:
            filter = Filter().kind(Kind(30017))
            events = await self.client.fetch_events_from(
                urls=[self.relay], filter=filter, timeout=timedelta(seconds=2)
            )
            return events
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve stalls: {e}")

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
            metadata = await self.client.fetch_metadata(
                public_key=author, timeout=timedelta(seconds=2)
            )
            return NostrProfile.from_metadata(metadata, author)
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve metadata: {e}")

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
            raise RuntimeError("Unable to connect to the relay")

        try:
            filter = Filter().kind(Kind(30017)).authors([seller])
            events = await self.client.fetch_events_from(
                urls=[self.relay], filter=filter, timeout=timedelta(seconds=2)
            )
            return events
        except Exception as e:
            raise RuntimeError(f"Unable to retrieve stalls: {e}")


def generate_and_save_keys(env_var: str, env_path: Optional[Path] = None) -> Keys:
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
        with open(env_path, "r") as f:
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
    with open(env_path, "w") as f:
        f.write("\n".join(new_lines))
        if new_lines:  # Add final newline if there's content
            f.write("\n")

    return keys
