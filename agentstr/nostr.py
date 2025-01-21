from typing import Optional
from os import getenv
import logging 

try: 
    import asyncio
except ImportError:
    raise ImportError("`asyncio` not installed. Please install using `pip install asyncio`")

try:
    from nostr_sdk import Keys, Client, EventBuilder, NostrSigner, SendEventOutput, Event, Metadata
except ImportError:
    raise ImportError("`nostr_sdk` not installed. Please install using `pip install nostr_sdk`")

class NostrClient():
   
    logger = logging.getLogger("NostrClient")
    ERROR: str = "ERROR"
    SUCCESS: str = "SUCCESS"
    
    def __init__(
        self,
        relay: str = None,
        nsec: str = None,
    ):
        """Initialize the Nostr client.

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
       
        self.relay = relay
        self.keys = Keys.parse(nsec)
        self.nostr_signer = NostrSigner.keys(self.keys)
        self.client = Client(self.nostr_signer)
            

    async def connect(
        self
    ) -> str:
        
        """Add relay to the NostrClient instance and connect to it.

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
        
    async def publish_text_note(
        self,
        text: str
    ) -> str:
        
        """Publish kind 1 event (text note) to the relay 

        Args:
            text: text to be published as kind 1 event

        Returns:
            str: event id if successful and "error" string if unsuccesful
        """
        builder = EventBuilder.text_note(text)

        try:
            output = await self.client.send_event_builder(builder)
            NostrClient.logger.info(f"Text note published with event id: {output.id.to_bech32()}")
            return output.id.to_bech32()
        except Exception as e:
            NostrClient.logger.error(f"Unable to publish text note to relay {self.relay}. Exception: {e}.")
            return NostrClient.ERROR

    async def publish_event(
        self,
        builder: EventBuilder
    ) -> str:
        
        """Publish generic Nostr event to the relay

        Returns:
            str: event id if successful or "error" string if unsuccesful
        """
        try:
            output = await self.client.send_event_builder(builder)
            NostrClient.logger.info(f"Event published with event id: {output.id.to_bech32()}")
            return output.id.to_bech32()
        except Exception as e:
            NostrClient.logger.error(f"Unable to publish event to relay {self.relay}. Exception: {e}.")
            return NostrClient.ERROR
    
    async def publish_profile(self, name: str, about: str, picture: str) -> str:
        """Publish a Nostr profile.

        Args:
            name: name of the Nostr profile
            about: brief description about the profile
            picture: url to a png file with a picture for the profile
        
        Returns:
            str: event id if successful or "error" string if unsuccesful
        """
        metadata_content = Metadata().set_name(name)
        metadata_content = metadata_content.set_about(about)
        metadata_content = metadata_content.set_picture(picture)

        builder = EventBuilder.metadata(metadata_content)
        try:
            output = await self.client.send_event_builder(builder)
            NostrClient.logger.info(f"Profile note published with event id: {output.id.to_bech32()}")
            return output.id.to_bech32()
        except Exception as e:
            NostrClient.logger.error(f"Unable to publish profile to relay {self.relay}. Exception: {e}.")
            return NostrClient.ERROR

    @classmethod
    def set_logging_level(cls, logging_level: int):
        """
        Set the logging level for the NostrClient logger.

        Args:
           logging_level (int): The logging level (e.g., logging.DEBUG, logging.INFO).
        """
        cls.logger.setLevel(logging_level)
        for handler in cls.logger.handlers:
           handler.setLevel(logging_level)
        cls.logger.info(f"Logging level set to {logging.getLevelName(logging_level)}")