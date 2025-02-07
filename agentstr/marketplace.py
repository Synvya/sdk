import logging
import json, ast, re
from typing import Optional, List, Tuple
from agentstr.nostr import Keys, NostrClient, ProductData, StallData, EventId, ShippingMethod, ShippingCost

try:
    from phi.tools import Toolkit
except ImportError:
    raise ImportError("`phidata` not installed. Please install using `pip install phidata`")



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

    
class Merchant(Toolkit):

    nostr_client: NostrClient = None
    # Product DB
    product_db = List[Tuple [ProductData, EventId | None]]

    # Stall DB
    stall_db = List[Tuple[StallData, EventId | None]]
   
    def __init__(
        self,
        merchant_profile: Profile,
        relay: str,
        stalls: List[StallData],
        products: List[ProductData]

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
        self.product_db = []
        for product in products:
            self.product_db.append((product, None))
    
        # initialize the Stall DB with no event id
        self.stall_db = []
        for stall in stalls:
            self.stall_db.append((stall, None))

        # Register all methods
        self.register(self.get_merchant_profile)
        self.register(self.get_merchant_relay)
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
    
    def get_merchant_profile(
        self
    ) -> str:
        """
        Retrieves merchant profile in JSON format

        Returns:
            str: merchant profile in JSON format
        """
        return json.dumps(self.merchant_profile.to_dict())
    
    def get_merchant_relay(self) -> str:
        return self.relay
    
    def get_products(
        self
    ) -> str:
        """
        Retrieves all the merchant products in JSON format

        Returns:
            str: JSON array with all products
        """
        products: List[ProductData] = [product for product, _ in self.product_db]
        dict_list: List[dict] = []
        for product in products:
            dict_list.append(self._product_to_dict(product))
        return json.dumps(dict_list)
    
    def get_stalls(
        self
    ) -> str:
        """
        Retrieves all the merchant stalls in JSON format

        Returns:
            str: JSON array with all stalls
        """
        output: List[str] = []
        for stall, _ in self.stall_db:
            output.append(stall.as_json())

        return json.dumps(output)
        
    def publish_all_products(
        self,
    ) -> str:
        """
        Publishes or updates all products sold by the merchant and adds the corresponding EventId to the Product DB

        Returns:
            str: JSON array with products that could NOT get published
        """

        #error_list: List[ProductData] = []
        error_list: List[dict] = []

        for i, (product, _) in enumerate(self.product_db):
            try:
                event_id = self.nostr_client.publish_product(product)
                self.product_db[i] = (product, event_id)
            except Exception as e:
                # add product to list of products not published
                Profile.logger.error(f"Unable to publish product {product}. Error {e}")
                error_list.append(self._product_to_dict(product))
                # error_list.append(product)

        #return error_list
        return json.dumps(error_list)
    
    def publish_all_stalls(
        self,
    ) -> str:
        """
        Publishes or updates all stalls managed by the merchant and adds the corresponding EventId to the Stall DB

        Returns:
            str: JSON array with stalls that could NOT get published
        """

        # error_list: List[StallData] = []
        output: List[str] = []

        for i, (stall, _) in enumerate(self.stall_db):
            try:
                event_id = self.nostr_client.publish_stall(stall)
                self.stall_db[i] = (stall, event_id)
            except Exception as e:
                # add stall to list of stalls not published
                Profile.logger.error(f"Unable to publish stall {stall}. Error {e}")
                # error_list.append(stall)
                output.append(stall.as_json())

        #return error_list
        return json.dumps(output)

    def publish_product(
        self,
        product: ProductData
    ) -> str:
        """
        Publishes or updates a specific product sold by the merchant and updates the Product DB

        Args:
            product: product 

        Returns:
            str: JSON array with published product or empty array if could not publish the product
        """

        dict_list: List[dict] = []

        try:
            event_id = self.nostr_client.publish_product(product)
            # find the product in the Product DB and update the EventId
            for i, product_tuple in enumerate(self.product_db):
                product_entry, _ = product_tuple
                if product_entry == product:
                    self.product_db[i] = (product_entry, event_id)
            
            # return JSON of the product
            dict_list.append(self._product_to_dict(product))
            return json.dumps(dict_list)
        except Exception as e:
            Profile.logger.error(f"Unable to publish product {product}. Error {e}")
            return json.dumps(dict_list)
    
    def publish_product_by_name(
        self,
        name: str
    ) -> str:
        """
        Publishes or updates the product sold by the merchant with a given name 
        Args:
            name: product name

        Returns:
            str: JSON array with published product or empty array if could not publish the product
        """
        error_dict_list: List[dict] = []

        # iterate through all products searching for the right name
        for product, _ in self.product_db:
            if product.name == name:
                return self.publish_product(product)
        
        # If we are here, then we didn't find a match
        return json.dumps(error_dict_list)
    
    def publish_products_by_stall(
        self,
        stall_name: str
    ) -> str:
        """
        Publishes or updates all products sold by the merchant in a given stall

        Returns:
            str: JSON array with products that could NOT get published
        
        Raises:
            ValueError: if no product is found for the given stall name
        """

        error_list: List[dict] = []
        stall_id = None

        # iterate through all stalls searching for the right name
        for stall, _ in self.stall_db:
            if stall.name() == stall_name:
                stall_id = stall.id()
        
        # if stall_id is empty, then we found no match
        if stall_id is None:
            raise ValueError(f"There are no products associated with stall name {stall_name}")
        
        # iterate through all the products and publish those belonging to this stall_id
        for product, _ in self.product_db:
            if product.stall_id == stall_id:
                output = self.publish_product(product)
                json_output = json.loads(output)
                # if there was an error publishing the product then add it to the error list
                if len(json_output) == 0:
                    error_list.append(self._product_to_dict(product))
            
        return json.dumps(error_list)
    
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
    
    def publish_stall(
        self,
        stall: StallData
    ) -> str:
        """
        Publishes or updates a specific stall managed by the merchant and updates the Stall DB

        Args:
            product: product 

        Returns:
            str: JSON array with the published stall
        """
        output: List[str] = []

        try:
            event_id = self.nostr_client.publish_stall(stall)
            # find the product in the Product DB and update the EventId
            for i, stall_tuple in enumerate(self.stall_db):
                stall_entry, _ = stall_tuple
                if stall_entry == stall:
                    self.stall_db[i] = (stall_entry, event_id)
            
            # add stall to output array
            output.append(stall.as_json())
        except Exception as e:
            Profile.logger.error(f"Unable to publish stall {stall}. Error {e}")
    
        return json.dumps(output)
        

    def publish_stall_by_name(
        self,
        name: str
    ) -> bool:
        """
        Publishes or updates the stall with a given name managed by the merchant

        Args:
            name: stall name

        Returns:
            bool: True if stall was published and False otherwise
        """

        # iterate through all stalls searching for the right name
        for stall, _ in self.stall_db:
            if stall.name == name:
                return self.publish_stall(stall)
        
        # If we are here, then we didn't find a match
        return False
    

    def _product_to_dict(
        self,
        product: ProductData
    ) -> dict:
        product_dict = {
            "id": product.id,
            "stall_id": product.stall_id,
            "name": product.name,
            "description": product.description,
            "images": product.images,
            "currency": product.currency,
            "price": product.price,
            "quantity": product.quantity,
            "specs": product.specs,
            "shipping": [{"id": shipping.id, "cost": shipping.cost} for shipping in product.shipping],
            "categories": product.categories
        }
        return product_dict

    



    
