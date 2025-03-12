"""
Module implementing the BuyerTools Toolkit for Agno agents.
"""

import json
from random import randint
from typing import Optional

from pydantic import ConfigDict

from synvya_sdk import NostrClient, Product, Profile, Stall

try:
    from agno.agent import AgentKnowledge  # type: ignore
    from agno.document.base import Document
    from agno.tools import Toolkit
    from agno.utils.log import logger
except ImportError as exc:
    raise ImportError(
        "`agno` not installed. Please install using `pip install agno`"
    ) from exc


def _map_location_to_geohash(location: str) -> str:
    """
    Map a location to a geohash.

    TBD: Implement this function. Returning a fixed geohash for now.

    Args:
        location: location to map to a geohash. Can be a zip code, city,
        state, country, or latitude and longitude.

    Returns:
        str: geohash of the location or empty string if location is not found
    """
    if "snoqualmie" in location.lower():
        return "C23Q7U36W"

    return ""


class BuyerTools(Toolkit):
    """
    BuyerTools is a toolkit that allows an agent to find sellers and
    transact with them over Nostr.

    `Download` tools download data from the Nostr relay and store it in the
    knowledge base.

    `Get` tools retrieve data from the knowledge base.

    TBD: populate the sellers locations with info from stalls.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, extra="allow", validate_assignment=True
    )

    def __init__(
        self,
        knowledge_base: AgentKnowledge,
        relay: str,
        private_key: str,
    ) -> None:
        """Initialize the Buyer toolkit.

        Args:
            knowledge_base: knowledge base of the buyer agent
            relay: Nostr relay to use for communications
            private_key: private key of the buyer using this agent
        """
        super().__init__(name="Buyer")
        self.relay = relay
        self.private_key = private_key
        self.knowledge_base = knowledge_base
        # Initialize fields
        self._nostr_client = NostrClient(relay, private_key)
        self._nostr_client.set_logging_level(logger.getEffectiveLevel())
        self.profile = self._nostr_client.get_profile()
        self.sellers: set[Profile] = set()

        # Register methods
        self.register(self.download_all_sellers)
        self.register(self.download_products_from_seller)
        self.register(self.download_sellers_from_marketplace)
        self.register(self.download_stalls_from_seller)
        self.register(self.get_all_products_from_knowledge_base)
        self.register(self.get_all_sellers_from_knowledge_base)
        self.register(self.get_all_stalls_from_knowledge_base)
        self.register(self.get_own_profile)
        self.register(self.get_products_from_knowledge_base_by_category)
        self.register(self.get_relay)
        self.register(self.purchase_product)

    def download_all_sellers(self) -> str:
        """
        Download all sellers from the Nostr relay and store their Nostr
        profile in the knowledge base.

        A seller is defined as a Nostr profile that has published a stall.

        Returns:
            str: JSON string with status and count of sellers refreshed
        """
        logger.debug("Downloading all sellers from the Nostr relay")
        try:
            self.sellers = self._nostr_client.retrieve_all_merchants()
            for seller in self.sellers:
                self._store_profile_in_kb(seller)
            response = json.dumps({"status": "success", "count": len(self.sellers)})
        except RuntimeError as e:
            logger.error("Error downloading all sellers from the Nostr relay: %s", e)
            response = json.dumps({"status": "error", "message": str(e)})

        return response

    def download_products_from_seller(self, public_key: str) -> str:
        """
        Download all products published by a seller on Nostr and store them
        in the knowledge base.

        Args:
            public_key: public key of the seller

        Returns:
            str: JSON string with all products published by the seller
        """
        logger.debug("Downloading products from seller %s", public_key)
        try:
            # retrieve products from the Nostr relay
            products = self._nostr_client.retrieve_products_from_merchant(public_key)

            # store products in the knowledge base
            for product in products:
                self._store_product_in_kb(product)

            response = json.dumps([product.to_dict() for product in products])

        except RuntimeError as e:
            logger.error("Error downloading products from seller %s: %s", public_key, e)
            response = json.dumps({"status": "error", "message": str(e)})

        return response

    def download_sellers_from_marketplace(self, public_key: str, name: str) -> str:
        """
        Download sellers included in a Nostr marketplace and store their Nostr
        profile in the knowledge base.

        Args:
            public_key: bech32 encoded public key of the owner of the marketplace
            name: name of the marketplace to download sellers from

        Returns:
            str: JSON string with status and count of sellers downloaded
        """
        logger.debug("Downloading sellers from the Nostr marketplace %s", name)
        try:
            # Retrieve sellers from the Nostr marketplace
            self.sellers = self._nostr_client.retrieve_marketplace_merchants(
                public_key, name
            )
            # Store sellers in the knowledge base
            for seller in self.sellers:
                self._store_profile_in_kb(seller)

            # Return the number of sellers downloaded
            response = json.dumps({"status": "success", "count": len(self.sellers)})
        except RuntimeError as e:
            logger.error(
                "Error downloading sellers from the Nostr marketplace %s: %s", name, e
            )
            response = json.dumps({"status": "error", "message": str(e)})

        return response

    def download_stalls_from_seller(self, public_key: str) -> str:
        """
        Download all stalls published by a seller on Nostr and store them
        in the knowledge base.

        Args:
            public_key: public key of the seller

        Returns:
            str: JSON string with all stalls published by the seller
        """
        logger.debug("Downloading stalls from seller %s", public_key)
        try:
            # retrieve stalls from the Nostr relay
            stalls = self._nostr_client.retrieve_stalls_from_merchant(public_key)

            # store stalls in the knowledge base
            for stall in stalls:
                self._store_stall_in_kb(stall)

            # convert stalls to JSON string
            response = json.dumps([stall.to_dict() for stall in stalls])
        except RuntimeError as e:
            logger.error("Error downloading stalls from seller %s: %s", public_key, e)
            response = json.dumps({"status": "error", "message": str(e)})

        return response

    def get_all_products_from_knowledge_base(self) -> str:
        """Get the list of products stored in the knowledge base.

        Returns:
            str: JSON string of products
        """
        logger.debug("Getting products from knowledge base")
        documents = self.knowledge_base.search(
            query="", num_documents=100, filters=[{"type": "product"}]
        )
        for doc in documents:
            logger.debug("Document: %s", doc.to_dict())

        products_json = [doc.content for doc in documents]
        logger.debug("Found %d products in the knowledge base", len(products_json))
        return json.dumps(products_json)

    def get_all_sellers_from_knowledge_base(self) -> str:
        """Get the list of sellers stored in the knowledge base.

        Returns:
            str: JSON string of sellers
        """
        logger.debug("Getting sellers from knowledge base")

        documents = self.knowledge_base.search(
            query="", num_documents=100, filters=[{"type": "seller"}]
        )
        for doc in documents:
            logger.debug("Document: %s", doc.to_dict())

        sellers_json = [doc.content for doc in documents]
        logger.debug("Found %d sellers in the knowledge base", len(sellers_json))
        return json.dumps(sellers_json)

    def get_all_stalls_from_knowledge_base(self) -> str:
        """Get the list of stalls stored in the knowledge base.

        Returns:
            str: JSON string of stalls
        """
        logger.debug("Getting stalls from knowledge base")
        documents = self.knowledge_base.search(
            query="", num_documents=100, filters=[{"type": "stall"}]
        )
        for doc in documents:
            logger.debug("Document: %s", doc.to_dict())

        stalls_json = [doc.content for doc in documents]
        logger.debug("Found %d stalls in the knowledge base", len(stalls_json))
        return json.dumps(stalls_json)

    def get_own_profile(self) -> str:
        """Get the Nostr profile of the buyer agent.

        Returns:
            str: buyer profile json string
        """
        logger.debug("Getting own profile")
        return self.profile.to_json()

    def get_products_from_knowledge_base_by_category(self, category: str) -> str:
        """
        Get the list of products stored in the knowledge base for a given category.

        Returns:
            str: JSON string of products
        """
        logger.debug("Getting products from knowledge base by category: %s", category)

        search_filters = [
            {"type": "product"},
            {"categories": [category]},
        ]

        documents = self.knowledge_base.search(
            query="",
            num_documents=100,
            filters=search_filters,
        )

        logger.debug("Found %d documents with category %s", len(documents), category)
        for doc in documents:
            logger.debug("Document: %s", doc.to_dict())

        products_json = [doc.content for doc in documents]
        return json.dumps(products_json)

    def get_relay(self) -> str:
        """Get the Nostr relay that the buyer agent is using.

        Returns:
            str: Nostr relay
        """
        return self.relay

    def purchase_product(self, product_name: str, quantity: int) -> str:
        """
        Purchase a product.

        TBD: Implement this function. Returning a fixed message for now.

        Args:
            product_name: name of the product to purchase
            quantity: quantity of the product to purchase

        Returns:
            str: JSON string with status and message
        """
        logger.info("Purchasing product: %s", product_name)

        try:
            product = self._get_product_from_kb(product_name)
        except RuntimeError as e:
            logger.error("Error getting product from knowledge base: %s", e)
            return json.dumps({"status": "error", "message": str(e)})

        # Choosing the first shipping zone for now
        # Address is hardcoded for now. Add it to the buyer profile later.
        order_msg = self._create_order(
            product.id,
            quantity,
            product.shipping[0].get_id(),
            "123 Main St, Anytown, USA",
        )

        self._nostr_client.send_private_message(
            product.get_seller(),
            order_msg,
        )

        return json.dumps(
            {
                "status": "success",
                "message": f"Product {product_name} purchased from seller {product.get_seller()}",
            }
        )

    def _create_order(
        self,
        product_id: str,
        quantity: int,
        shipping_id: str,
        address: Optional[str] = None,
    ) -> str:
        random_order_id = randint(
            0, 999999999
        )  # Generate a number between 0 and 999999999
        order_id_str = f"{random_order_id:09d}"

        order = {
            "id": order_id_str,
            "type": 0,
            "name": self.profile.name,
            "address": address,
            "message": "Please accept this order.",
            "contact": {
                "nostr": self.profile.public_key,
                "phone": "",
                "email": "",
            },
            "items": [{"product_id": product_id, "quantity": quantity}],
            "shipping_id": shipping_id,
        }

        return json.dumps(
            order, indent=2
        )  # Convert to JSON string with pretty printing

    def _get_product_from_kb(self, product_name: str) -> Product:
        """
        Get a product from the knowledge base.
        """
        logger.debug("Getting product from knowledge base: %s", product_name)
        documents = self.knowledge_base.search(
            query=product_name, num_documents=1, filters=[{"type": "product"}]
        )
        if len(documents) == 0:
            raise RuntimeError(f"Product {product_name} not found in knowledge base")
        return Product.from_json(documents[0].content)

    def _store_profile_in_kb(self, profile: Profile) -> None:
        """
        Store a Nostr profile in the knowledge base.

        Args:
            profile: Nostr profile to store
        """
        logger.debug("Storing profile in knowledge base: %s", profile.name)

        doc = Document(
            content=profile.to_json(),
            name=profile.name,
            meta_data={"type": "seller"},
        )

        # Store response
        self.knowledge_base.load_document(document=doc, filters=[{"type": "seller"}])

    def _store_product_in_kb(self, product: Product) -> None:
        """
        Store a Nostr product in the knowledge base.

        Args:
            product: Nostr product to store
        """
        logger.debug("Storing product in knowledge base: %s", product.name)

        doc = Document(
            content=product.to_json(),
            name=product.name,
            meta_data={"type": "product"},
        )

        # Store response
        self.knowledge_base.load_document(
            document=doc,
            filters=[{"type": "product"}, {"categories": product.categories}],
        )

    def _store_stall_in_kb(self, stall: Stall) -> None:
        """
        Store a Nostr stall in the knowledge base.

        Args:
            stall: Nostr stall to store
        """
        logger.debug("Storing stall in knowledge base: %s", stall.name)

        doc = Document(
            content=stall.to_json(),
            name=stall.name,
            meta_data={"type": "stall"},
        )

        # Store response
        self.knowledge_base.load_document(document=doc, filters=[{"type": "stall"}])
