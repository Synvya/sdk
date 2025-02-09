import logging 
from typing import Optional
try: 
    import asyncio
except ImportError:
    raise ImportError("`asyncio` not installed. Please install using `pip install asyncio`")

try:
    from nostr_sdk import Keys, Client, EventBuilder, NostrSigner, EventId, ShippingCost, ShippingMethod
    from nostr_sdk import Metadata, StallData, ProductData, Tag, Coordinate, Kind, PublicKey, Timestamp, Kind, Event

except ImportError:
    raise ImportError("`nostr_sdk` not installed. Please install using `pip install nostr_sdk`")

class NostrClient():

    """
    NostrClient implements the set of Nostr utilities required for higher level functions implementing
    like the Marketplace.

    Nostr is an asynchronous communication protocol. To hide this, NostrClient exposes synchronous functions.
    Users of the NostrClient should ignore `_async_` functions which are for internal purposes only.   
    """
   
    logger = logging.getLogger("NostrClient")
    ERROR: str = "ERROR"
    SUCCESS: str = "SUCCESS"
    
    
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
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            NostrClient.logger.addHandler(console_handler)
       
        # configure relay and keys for the client
        self.relay = relay
        self.keys = Keys.parse(nsec)
        self.nostr_signer = NostrSigner.keys(self.keys)
        self.client = Client(self.nostr_signer)

  
    def delete_event(
        self,
        event_id: EventId,
        reason: Optional[str] = None
    ) -> EventId:
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
        
    def publish_event(
        self,
        event_builder: EventBuilder
    ) -> EventId:
        """
        Publish generic Nostr event to the relay

        Returns:
            EventId: event id if successful or NostrClient.ERROR if unsuccesful
        
        Raises:
            RuntimeError: if the product can't be published   
        """
        # Run the async publishing function synchronously
        return asyncio.run(self._async_publish_event(event_builder))
    
    def publish_note(
        self,
        text: str
    ) -> EventId:
        """Publish note with event kind 1 

        Args:
            text: text to be published as kind 1 event

        Returns:
            EventId: EventId if successful or NostrClient.ERROR if unsuccesful
        
        Raises:
            RuntimeError: if the product can't be published
        """
        # Run the async publishing function synchronously
        return asyncio.run(self._async_publish_note(text))
       
    def publish_product(
        self,
        product: ProductData
    ) -> EventId:
        """
        Create or update a NIP-15 Marketplace product with event kind 30018

        Args:
            product: product to be published

        Returns:
            EventId: event id if successful or NostrClient.ERROR if unsuccesful 
        
        Raises:
            RuntimeError: if the product can't be published
        """
        # Run the async publishing function synchronously
        return asyncio.run(
            self._async_publish_product(product)
        )

    def publish_profile(
        self,
        name: str,
        about: str,
        picture: str
    ) -> EventId:
        """
        Publish a Nostr profile with event kind 0

        Args:
            name: name of the Nostr profile
            about: brief description about the profile
            picture: url to a png file with a picture for the profile
        
        Returns:
            EventId: event id if successful or NostrClient.ERROR if unsuccesful
        
        Raises:
            RuntimeError: if the profile can't be published
        """
        # Run the async publishing function synchronously
        return asyncio.run(
            self._async_publish_profile(
                name, 
                about,
                picture
            )
        )

    def publish_stall(
        self,
        stall: StallData
    ) -> EventId:
        """Publish a stall to nostr
        
        Args:
            stall: stall to be published

        Returns:
            EventId: event id if successful or NostrClient.ERROR if unsuccesful
        """
        try:
            return asyncio.run(
                self._async_publish_stall(stall)
            )
        except Exception as e:
            self.logger.error(f"Failed to publish stall: {e}")
            return NostrClient.ERROR
    
    @classmethod
    def set_logging_level(
        cls,
        logging_level: int
    ):
        """
        Set the logging level for the NostrClient logger.

        Args:
           logging_level (int): The logging level (e.g., logging.DEBUG, logging.INFO).
        """

        cls.logger.setLevel(logging_level)
        for handler in cls.logger.handlers:
           handler.setLevel(logging_level)
        cls.logger.info(f"Logging level set to {logging.getLevelName(logging_level)}")

    # ----------------------------------------------------------------------------------------------
    # --*-- async functions for internal use only. Developers should use synchronous functions above
    # ----------------------------------------------------------------------------------------------
    
    async def _async_connect(
        self
    ) -> str:
        
        """Asynchronous function to add relay to the NostrClient instance and connect to it.

        Returns:
            str: NostrClient.SUCCESS or NostrClient.ERROR
        """
        try:
            await self.client.add_relay(self.relay)
            NostrClient.logger.info(f"Relay {self.relay} succesfully added.")
            await self.client.connect()
            NostrClient.logger.info("Connected to relay.")
            return NostrClient.SUCCESS
        except Exception as e:
            NostrClient.logger.error(f"Unable to connect to relay {self.relay}. Exception: {e}.")
            return NostrClient.ERROR
          
    async def _async_publish_event(
        self,
        event_builder: EventBuilder
    ) -> EventId:
        """
        Publish generic Nostr event to the relay

        Returns:
            EventId: event id of the published event
        
        Raises:
            RuntimeError: if the event can't be published
        """
        connected = await self._async_connect()

        if (connected == NostrClient.ERROR):
            raise RuntimeError("Unable to connect to the relay")

        try:
            output = await self.client.send_event_builder(event_builder)
            if len(output.success) > 0:
                NostrClient.logger.info(f"Event published with event id: {output.id.to_bech32()}")
                return output.id
            else:
                raise RuntimeError("Unable to publish event")
        except Exception as e:
            NostrClient.logger.error(f"NostrClient instance not properly initialized. Exception: {e}.")
            raise RuntimeError(f"NostrClient instance not properly initialized. Exception: {e}.")

    async def _async_publish_note(
        self,
        text: str
    ) -> EventId:
        """
        Asynchronous funcion to publish kind 1 event (text note) to the relay 

        Args:
            text: text to be published as kind 1 event

        Returns:
            EventId: event id if successful or NostrClient.ERROR if unsuccesful
        
        Raises:
            RuntimeError: if the event can't be published
        """
        event_builder = EventBuilder.text_note(text)
        return await self._async_publish_event(event_builder)

    async def _async_publish_product(
        self,
        product: ProductData
    ) -> EventId:
        """
        Asynchronous function to create or update a NIP-15 Marketplace product with event kind 30018
        
        Args:
            product: product to publish

        Returns:
            EventId: event id if successful or NostrClient.ERROR if unsuccesfull
        
        Raises:
            RuntimeError: if the product can't be published
        """
        coordinate_tag = Coordinate(Kind(30017), self.keys.public_key(), product.stall_id)
                
        # EventBuilder.product_data() has a bug with tag handling.
        # We use the function to create the content field and discard the eventbuilder 
        bad_event_builder = EventBuilder.product_data(product)

        # create an event from bad_event_builder to extract the content - not broadcasted
        bad_event = await self.client.sign_event_builder(bad_event_builder)
        content = bad_event.content()
    
        # build a new event with the right tags and the content
        good_event_builder = EventBuilder(Kind(30018), content).tags([Tag.identifier(product.id), Tag.coordinate(coordinate_tag)])
        self.logger.info("Product event: " + str(good_event_builder))
        return await self._async_publish_event(good_event_builder)
          
    async def _async_publish_profile(
        self,
        name: str,
        about: str,
        picture: str
    ) -> EventId:
        """
        Asynchronous function to publish a Nostr profile with event kind 0

        Args:
            name: name of the Nostr profile
            about: brief description about the profile
            picture: url to a png file with a picture for the profile
        
        Returns:
            EventId: event id if successful or NostrClient.ERROR if unsuccesful

        Raises:
            RuntimeError: if the profile can't be published
        """
        metadata_content = Metadata().set_name(name)
        metadata_content = metadata_content.set_about(about)
        metadata_content = metadata_content.set_picture(picture)

        event_builder = EventBuilder.metadata(metadata_content)
        return await self._async_publish_event(event_builder)
    
    async def _async_publish_stall(
        self,
        stall: StallData
    ) -> EventId:
        """
        Asynchronous function to create or update a NIP-15 Marketplace stall with event kind 30017

        Args:
            stall: stall to be published

        Returns:
            EventId: event id if successful or NostrClient.ERROR if unsuccesfull
        
        Raises:
            RuntimeError: if the profile can't be published
        """

        self.logger.info(f"Stall: {stall}")
        event_builder = EventBuilder.stall_data(stall)
        return await self._async_publish_event(event_builder)