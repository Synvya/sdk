import logging
import json, ast, re
from typing import Optional, List, Tuple, Dict, Any, Union
from agentstr.nostr import Keys, NostrClient, ProductData, StallData, EventId, ShippingMethod, ShippingCost

try:
    from phi.tools import Toolkit
except ImportError:
    raise ImportError("`phidata` not installed. Please install using `pip install phidata`")

from pydantic import ConfigDict, BaseModel, Field, validate_call


class Profile():

    logger = logging.getLogger("Profile")
    WEB_URL: str = "https://primal.net/p/"
    
    
    def __init__(
        self,
        name: str,
        about: str,
        picture: str,
        nsec: Optional[str] = None
    ):
        """Initialize the profile.

        Args:
            name: Name for the merchant
            about: brief description about the merchant
            picture: url to a png file with a picture for the merchant
            nsec: optional private key to be used by this Merchant 
        """

        # Set log handling for MerchantProfile
        if not Profile.logger.hasHandlers():
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            Profile.logger.addHandler(console_handler)
        
        self.name = name
        self.about = about
        self.picture = picture
               
        if nsec:
            self.private_key = nsec
            keys = Keys.parse(self.private_key)
            self.public_key = keys.public_key().to_bech32()
            Profile.logger.info(f"Pre-defined private key reused for {self.name}: {self.private_key}")
            Profile.logger.info(f"Pre-defined public key reused for {self.name}: {self.public_key}")
        else:
            keys = Keys.generate()
            self.private_key = keys.secret_key().to_bech32()
            self.public_key = keys.public_key().to_bech32()
            Profile.logger.info(f"New private key created for {self.name}: {self.private_key}")
            Profile.logger.info(f"New public key created for {self.name}: {self.public_key}")
        
        self.url = self.WEB_URL + self.public_key

        # Register all methods
        # self.register(self.get_about)
        # self.register(self.get_name)
        # self.register(self.get_picture)
        # self.register(self.get_private_key)
        # self.register(self.get_public_key)
        # self.register(self.get_url)

    def __str__(self):
        return (
            "Merchant Profile:\n" 
            "Name = {}\n"
            "Description = {}\n"
            "Picture = {}\n"
            "URL = {}\n"
            "Private key = {}\n"
            "Public key = {}".format(
                self.name, self.about, self.picture,
                self.url, self.private_key, self.public_key
            )
        )
    
    def to_dict(
        self
    ):
        return {
            'name': self.name,
            'description': self.about,
            'picture': self.picture,
            'public key': self.public_key,
            'private key': self.private_key
        }
   
    def get_about(self) -> str:
        """
        Returns a description of the Merchant

        Returns:
            str: description of the Merchant
        """
        return self.about
    
    def get_name(self) -> str:
        """
        Returns the Merchant's name

        Returns:
            str: Merchant's name
        """
        return self.name    

    def get_picture(self) -> str:
        """
        Returns the picture associated with the Merchant.

        Returns:
            str: URL to the picture associated with the Merchant
        """
        return self.picture
    
    def get_private_key(self) -> str:
        """
        Returns the private key.

        Returns:
            str: private key in bech32 format
        """
        return self.private_key
    
    def get_public_key(self) -> str:
        """
        Returns the public key.

        Returns:
            str: public key in bech32 format
        """
        return self.public_key
    
    def get_url(self) -> str:
        return self.url

    
class MerchantProduct(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    stall_id: str
    name: str
    description: str
    images: List[str]
    currency: str
    price: float
    quantity: int
    shipping: List[ShippingCost]
    categories: Optional[List[str]] = []
    specs: Optional[List[List[str]]] = []

    @classmethod
    def from_product_data(cls, product: ProductData) -> "MerchantProduct":
        return cls(
            id=product.id,
            stall_id=product.stall_id,
            name=product.name,
            description=product.description,
            images=product.images,
            currency=product.currency,
            price=product.price,
            quantity=product.quantity,
            shipping=product.shipping,
            categories=product.categories if product.categories is not None else [],
            specs=product.specs if product.specs is not None else []
        )

    def to_product_data(self) -> ProductData:
        return ProductData(
            id=self.id,
            stall_id=self.stall_id,
            name=self.name,
            description=self.description,
            images=self.images,
            currency=self.currency,
            price=self.price,
            quantity=self.quantity,
            shipping=self.shipping,  
            categories=self.categories,
            specs=self.specs
        )

class MerchantStall(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    name: str
    description: str
    currency: str
    shipping: List[ShippingMethod]

    @classmethod
    def from_stall_data(cls, stall: StallData) -> "MerchantStall":
        return cls(
            id=stall.id(),
            name=stall.name(),
            description=stall.description(),
            currency=stall.currency(),
            shipping=stall.shipping()
        )

    def to_stall_data(self) -> StallData:
        return StallData(
            self.id,
            self.name,
            self.description,
            self.currency,
            self.shipping  # No conversion needed
        )

class Merchant(Toolkit):

    """
    Merchant is a toolkit that allows a merchant to publish products and stalls to Nostr.

    TBD:
    - Change all interactions with phidata agents to use MerchantProduct and MerchantStall
    - Internal functions should use ProductData and StallData
    """

    from pydantic import ConfigDict
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra='allow',
        validate_assignment=True
    )

    nostr_client: Optional[NostrClient] = None
    product_db: List[Tuple[MerchantProduct, Optional[EventId]]] = []
    stall_db: List[Tuple[StallData, Optional[EventId]]] = []
    
   
    def __init__(
        self,
        merchant_profile: Profile,
        relay: str,
        stalls: List[StallData],
        products: List[MerchantProduct]
    ):
        """Initialize the Merchant toolkit.

        Args:
            merchant_profile: profile of the merchant using this agent
            relay: Nostr relay to use for communications
            stalls: list of stalls managed by this merchant
            products: list of products sold by this merchant
        """
        super().__init__(name="merchant")
        self.relay = relay
        self.merchant_profile = merchant_profile
        self.nostr_client = NostrClient(self.relay, self.merchant_profile.get_private_key())

        # initialize the Product DB with no event id
        self.product_db = [(product, None) for product in products]
    
        # initialize the Stall DB with no event id
        self.stall_db = [(stall, None) for stall in stalls]

        # Register wrapped versions of the methods
        self.register(self.get_profile)
        self.register(self.get_relay)
        self.register(self.get_products)
        self.register(self.get_stalls)
        self.register(self.publish_all_products)
        self.register(self.publish_all_stalls)
        self.register(self.publish_product)
        self.register(self.publish_product_by_name)
        self.register(self.publish_products_by_stall)
        self.register(self.publish_profile)
        self.register(self.publish_stall)
        self.register(self.publish_stall_by_name)
    
    def get_profile(
        self
    ) -> str:
        """
        Retrieves merchant profile in JSON format

        Returns:
            str: merchant profile in JSON format
        """
        return json.dumps(self.merchant_profile.to_dict())
    
    def get_relay(self) -> str:
        return self.relay
    
    def get_products(self) -> List[MerchantProduct]:
        """
        Retrieves all the merchant products
        
        Returns:
            List[MerchantProduct]: List of MerchantProducts
        """
        return [product for product, _ in self.product_db]
    
    def get_stalls(self) -> str:
        """
        Retrieves all the merchant stalls in JSON format
        
        Returns:
            str: JSON string containing all stalls
        """
        stalls = [MerchantStall.from_stall_data(s) for s, _ in self.stall_db]
        return json.dumps([s.dict() for s in stalls])
    
    def publish_all_products(
        self,
    ) -> str:
        """
        Publishes or updates all products sold by the merchant and adds the corresponding EventId to the Product DB

        Returns:
            str: JSON array with status of all product publishing operations
        """
        results = []

        for i, (product, _) in enumerate(self.product_db):
            try:
                # Convert MerchantProduct to ProductData for nostr_client
                product_data = product.to_product_data()
                # Publish using the SDK's synchronous method
                event_id = self.nostr_client.publish_product(product_data)
                self.product_db[i] = (product, event_id)
                results.append({
                    "status": "success",
                    "event_id": str(event_id),
                    "product_name": product.name
                })
            except Exception as e:
                Profile.logger.error(f"Unable to publish product {product}. Error {e}")
                results.append({
                    "status": "error",
                    "message": str(e),
                    "product_name": product.name
                })

        return json.dumps(results)
    
    def publish_all_stalls(
        self,
    ) -> str:
        """
        Publishes or updates all stalls managed by the merchant and adds the corresponding EventId to the Stall DB

        Returns:
            str: JSON array with status of all stall publishing operations
        """
        results = []

        for i, (stall, _) in enumerate(self.stall_db):
            try:
                event_id = self.nostr_client.publish_stall(stall)
                self.stall_db[i] = (stall, event_id)
                results.append({
                    "status": "success",
                    "event_id": str(event_id),
                    "stall_name": stall.name()
                })
            except Exception as e:
                Profile.logger.error(f"Unable to publish stall {stall}. Error {e}")
                results.append({
                    "status": "error",
                    "message": str(e),
                    "stall_name": stall.name()
                })

        return json.dumps(results)

    def publish_product(self, product: MerchantProduct) -> str:
        """Publish a product to nostr
        
        Args:
            product: MerchantProduct to be published
            
        Returns:
            str: JSON string with status of the operation
        """
        try:
            # Convert MerchantProduct to ProductData for nostr_client
            product_data = product.to_product_data()
            # Publish using the SDK's synchronous method
            print(f"DEBUG: made it past the conversion from MerchantProduct to ProductData")
            event_id = self.nostr_client.publish_product(product_data)
            return json.dumps({
                "status": "success",
                "event_id": str(event_id),
                "product_name": product.name
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e),
                "product_name": product.name
            })

    def publish_product_by_name(
        self,
        name: str
    ) -> str:
        """
        Publishes or updates the product sold by the merchant with a given name 
        Args:
            name: product name

        Returns:
            str: JSON string with status of the operation
        """
        # iterate through all products searching for the right name
        for product, _ in self.product_db:
            if product.name == name:
                return self.publish_product(product)
        
        # If we are here, then we didn't find a match
        return json.dumps({
            "status": "error",
            "message": f"Product '{name}' not found in database",
            "product_name": name
        })
    
    def publish_products_by_stall(
        self,
        stall_name: str
    ) -> str:
        """
        Publishes or updates all products sold by the merchant in a given stall

        Args:
            stall_name: name of the stall containing the products

        Returns:
            str: JSON array with status of all product publishing operations
        """
        results = []
        stall_id = None

        # iterate through all stalls searching for the right name
        for stall, _ in self.stall_db:
            if stall.name() == stall_name:
                stall_id = stall.id()
                break
        
        # if stall_id is empty, then we found no match
        if stall_id is None:
            return json.dumps([{
                "status": "error",
                "message": f"Stall '{stall_name}' not found in database",
                "stall_name": stall_name
            }])
        
        # iterate through all the products and publish those belonging to this stall_id
        for product, _ in self.product_db:
            if product.stall_id == stall_id:
                try:
                    result = json.loads(self.publish_product(product))
                    result["stall_name"] = stall_name
                    results.append(result)
                except Exception as e:
                    Profile.logger.error(f"Unable to publish product {product}. Error {e}")
                    results.append({
                        "status": "error",
                        "message": str(e),
                        "product_name": product.name,
                        "stall_name": stall_name
                    })
        
        if not results:
            return json.dumps([{
                "status": "error",
                "message": f"No products found in stall '{stall_name}'",
                "stall_name": stall_name
            }])
            
        return json.dumps(results)
    
    def publish_profile(
        self
    ) -> str:
        """
        Publishes the profile on Nostr

        Returns:
            str: JSON of the event that published the profile
        
        Raises:
            RuntimeError: if it can't publish the event
        """
        try:
            event_id = self.nostr_client.publish_profile(
                self.merchant_profile.get_name(),
                self.merchant_profile.get_about(),
                self.merchant_profile.get_picture()
            )
            return json.dumps(event_id.__dict__)
        except Exception as e:
            raise RuntimeError(f"Unable to publish the profile: {e}")
    
    def publish_stall(self, stall: MerchantStall) -> str:
        """Publish a stall to nostr
        
        Args:
            stall: MerchantStall to be published
            
        Returns:
            str: JSON string with status of the operation
        """
        try:
            # Convert the MerchantStall to SDK type
            stall_data = stall.to_stall_data()
            # Publish using the SDK's synchronous method
            event_id = self.nostr_client.publish_stall(stall_data)
            return json.dumps({
                "status": "success",
                "event_id": str(event_id),
                "stall_name": stall.name
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e),
                "stall_name": stall.name
            })

    def publish_stall_by_name(self, arguments: str) -> str:
        """Publish a stall by name
        
        Args:
            arguments: JSON string that may contain {"name": "stall_name"} or just "stall_name"
            
        Returns:
            str: JSON string with status of the operation
        """
        try:
            # Try to parse as JSON first
            import json
            if isinstance(arguments, dict):
                parsed = arguments
            else:
                parsed = json.loads(arguments)
            stall_name = parsed.get("name", parsed)  # Get name if exists, otherwise use whole value
        except json.JSONDecodeError:
            # If not JSON, use the raw string
            stall_name = arguments
        
        # Find the stall in stall_db
        for stall, _ in self.stall_db:
            if stall.name() == stall_name:
                # Convert SDK StallData to our MerchantStall
                merchant_stall = MerchantStall.from_stall_data(stall)
                # Publish the stall
                return self.publish_stall(merchant_stall)
        
        return json.dumps({
            "status": "error", 
            "message": f"Stall '{stall_name}' not found in database"
        })

    



    
