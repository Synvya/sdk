import logging
from typing import Optional
from . import nostr 

try:
    from phi.tools import Toolkit
except ImportError:
    raise ImportError("`phidata` not installed. Please install using `pip install phidata`")

try: 
    import asyncio
except ImportError:
    raise ImportError("`asyncio` not installed. Please install using `pip install asyncio`")

class MerchantProfile():

    logger = logging.getLogger("MerchantProfile")
    
    def __init__(
        self,
        name: str,
        about: str,
        picture: str,
        nsec: Optional[str] = None
    ):
        """Initialize the Merchant profile.

        Args:
            name: Name for the merchant
            about: brief description about the merchant
            picture: url to a png file with a picture for the merchant
            nsec: private key to be used by this Merchant 
        """

        # Set log handling for MerchantProfile
        if not MerchantProfile.logger.hasHandlers():
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            MerchantProfile.logger.addHandler(console_handler)
        
        self.name = name
        self.about = about
        self.picture = picture

        if nsec:
            self.private_key = nsec
            keys = nostr.Keys.parse(self.private_key)
            self.public_key = keys.public_key().to_bech32()
            MerchantProfile.logger.info(f"Pre-defined private key reused for {self.name}: {self.private_key}")
            MerchantProfile.logger.info(f"Pre-defined public key reused for {self.name}: {self.public_key}")
        else:
            keys = nostr.Keys.generate()
            self.private_key = keys.secret_key().to_bech32()
            self.public_key = keys.public_key().to_bech32()
            MerchantProfile.logger.info(f"New private key created for {self.name}: {self.private_key}")
            MerchantProfile.logger.info(f"New public key created for {self.name}: {self.public_key}")
            
    def merchant_profile_to_str(self) -> str:
        return (
            f"Merchant name: {self.name}. "
            f"Merchant description: {self.about}. "
            f"Merchant picture URL: {self.picture}. "
            f"Private key: {self.private_key}. "
            f"Public key: {self.public_key}."
    )

    def get_public_key(self) -> str:
        return self.public_key
    
    def get_private_key(self) -> str:
        return self.private_key
    
    def get_name(self) -> str:
        return self.name
    
    def get_about(self) -> str:
        return self.about
    
    def get_picture(self) -> str:
        return self.picture
        


class Merchant(Toolkit):
    
    def __init__(
        self,
        merchant_profile: MerchantProfile,
        relay: str,
    ):
        """Initialize the Merchant toolkit.

        Args:
            merchant_profile: profile of the merchant using this agent
            relay: Nostr relay to use for communications
        """
        super().__init__(name="merchant")
        self.relay = relay
        self.merchant_profile = merchant_profile

        # Register all methods
        self.register(self.publish_merchant_profile)
    
    def publish_merchant_profile(
        self
    ) -> str:
        """
        Publishes the merchant profile on Nostr

        Returns:
            str: id of the event publishing the profile
        """
        # Run the async pubilshing function synchronously
        return asyncio.run(self._async_publish_merchant_profile())
    
    async def _async_publish_merchant_profile(
        self
    ) -> str:
        """
        Asynchronous method to publish the merchant profile on Nostr

        Returns:
            str: id of the event publishing the profile
        """
        
        nostr_client = nostr.NostrClient(self.relay, self.merchant_profile.get_private_key())
        await nostr_client.connect()
        eventid = await nostr_client.publish_profile(
            self.merchant_profile.get_name(),
            self.merchant_profile.get_about(),
            self.merchant_profile.get_picture()
        )
        return eventid
        