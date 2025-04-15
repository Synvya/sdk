"""
Module implementing the BuyerTools Toolkit for Agno agents.
"""

import json
import secrets
from typing import List, Optional

from pydantic import ConfigDict

from synvya_sdk import NostrClient, Product, Profile, ProfileFilter, Stall

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
        self.merchants: set[Profile] = set()

        # Register methods
        self.register(self.get_merchants)
        self.register(self.get_merchants_from_knowledge_base)
        self.register(self.get_merchants_in_marketplace)
        self.register(self.get_products)
        self.register(self.get_products_from_knowledge_base)
        # self.register(self.get_products_from_knowledge_base_by_category)
        self.register(self.get_profile)
        self.register(self.get_relay)
        self.register(self.get_stalls)
        self.register(self.get_stalls_from_knowledge_base)
        self.register(self.listen_for_message)
        self.register(self.submit_order)
        self.register(self.submit_payment)

    def get_merchants(self) -> str:
        """
        Download from the Nostr relay all merchants and store their Nostr
        profile in the knowledge base.

        Returns:
            str: JSON string with status and count of merchants refreshed
        """
        logger.debug("Downloading all merchants from the Nostr relay")
        try:
            self.merchants = self._nostr_client.get_merchants()
            for merchant in self.merchants:
                self._store_profile_in_kb(merchant)
            response = json.dumps({"status": "success", "count": len(self.merchants)})
        except RuntimeError as e:
            logger.error("Error downloading all merchants from the Nostr relay: %s", e)
            response = json.dumps({"status": "error", "message": str(e)})

        return response

    def get_merchants_from_knowledge_base(self) -> str:
        """
        Get the list of merchants stored in the knowledge base.

        Returns:
            str: JSON string of merchants
        """
        logger.debug("Getting merchants from knowledge base")

        documents = self.knowledge_base.search(
            query="", num_documents=100, filters=[{"type": "merchant"}]
        )
        for doc in documents:
            logger.debug("Document: %s", doc.to_dict())

        merchants_json = [doc.content for doc in documents]
        logger.debug("Found %d merchants in the knowledge base", len(merchants_json))
        return json.dumps(merchants_json)

    def get_merchants_in_marketplace(
        self,
        owner_public_key: str,
        name: str,
        profile_filter: Optional[ProfileFilter] = None,
    ) -> str:
        """
        Download from the Nostr relay all merchants included in a Nostr
        marketplace and store their Nostr profile in the knowledge base.

        Args:
            owner_public_key: bech32 encoded public key of the owner of the marketplace
            name: name of the marketplace to download merchants from

        Returns:
            str: JSON string with status and count of merchants downloaded

        TBD: Implement profile filter.
        """
        logger.debug("Downloading merchants from the Nostr marketplace %s", name)
        try:
            # Retrieve merchants from the Nostr marketplace
            self.merchants = self._nostr_client.get_merchants_in_marketplace(
                owner_public_key, name, profile_filter
            )
            # Store merchants in the knowledge base
            for merchant in self.merchants:
                self._store_profile_in_kb(merchant)

            # Return the number of merchants downloaded
            response = json.dumps({"status": "success", "count": len(self.merchants)})
        except RuntimeError as e:
            logger.error(
                "Error downloading merchants from the Nostr marketplace %s: %s",
                name,
                e,
            )
            response = json.dumps({"status": "error", "message": str(e)})

        return response

    def get_products(
        self, merchant_public_key: str, stall: Optional[Stall] = None
    ) -> str:
        """
        Download all products published by a merchant on Nostr and store them
        in the knowledge base.

        Args:
            merchant_public_key: public key of the merchant
            stall: optional stall to filter products by

        Returns:
            str: JSON string with all products published by the merchant
        """
        logger.debug("Downloading products from merchant %s", merchant_public_key)
        try:
            # retrieve products from the Nostr relay
            products = self._nostr_client.get_products(merchant_public_key, stall)

            # store products in the knowledge base
            for product in products:
                self._store_product_in_kb(product)

            response = json.dumps([product.to_dict() for product in products])

        except RuntimeError as e:
            logger.error(
                "Error downloading products from merchant %s: %s",
                merchant_public_key,
                e,
            )
            response = json.dumps({"status": "error", "message": str(e)})

        return response

    def get_products_from_knowledge_base(
        self,
        merchant_public_key: Optional[str] = None,
        categories: Optional[List[str]] = None,
    ) -> str:
        """
        Get a list of products stored in the knowledge base. Optionally filter by
        merchant or categories.

        Args:
            merchant_public_key: optional filter bymerchant
            categories: optional filter by the list of categories

        Returns:
            str: JSON string of products
        """
        logger.debug("Getting products from knowledge base")

        if merchant_public_key is not None:
            search_query = merchant_public_key
        else:
            search_query = ""

        if categories is not None:
            search_filters = [
                {"type": "product"},
                {"categories": categories},
            ]
        else:
            search_filters = [
                {"type": "product"},
            ]

        documents = self.knowledge_base.search(
            query=search_query, num_documents=100, filters=search_filters
        )
        for doc in documents:
            logger.debug("Document: %s", doc.to_dict())

        products_json = [doc.content for doc in documents]
        logger.debug("Found %d products in the knowledge base", len(products_json))
        return json.dumps(products_json)

    def get_profile(self) -> str:
        """
        Get the Nostr profile of the buyer agent.

        Returns:
            str: buyer profile json string
        """
        logger.debug("Getting own profile")
        return self.profile.to_json()

    def get_relay(self) -> str:
        """Get the Nostr relay that the buyer agent is using.

        Returns:
            str: Nostr relay
        """
        return self.relay

    def get_stalls(self, merchant_public_key: str) -> str:
        """
        Download all stalls published by a merchant on Nostr and store them
        in the knowledge base.

        Args:
            merchant_public_key: public key of the merchant

        Returns:
            str: JSON string with all stalls published by the merchant
        """
        logger.debug("Downloading stalls from merchant %s", merchant_public_key)
        try:
            # retrieve stalls from the Nostr relay
            stalls = self._nostr_client.get_stalls(merchant_public_key)

            # store stalls in the knowledge base
            for stall in stalls:
                self._store_stall_in_kb(stall)

            # convert stalls to JSON string
            response = json.dumps([stall.to_dict() for stall in stalls])
        except RuntimeError as e:
            logger.error(
                "Error downloading stalls from merchant %s: %s",
                merchant_public_key,
                e,
            )
            response = json.dumps({"status": "error", "message": str(e)})

        return response

    def get_stalls_from_knowledge_base(
        self, merchant_public_key: Optional[str] = None
    ) -> str:
        """
        Get the list of stalls stored in the knowledge base.
        Optionally filter by merchant.

        Args:
            merchant_public_key: optional filter by merchant

        Returns:
            str: JSON string of stalls
        """
        logger.debug("Getting stalls from knowledge base")

        if merchant_public_key is not None:
            search_query = merchant_public_key
        else:
            search_query = ""

        documents = self.knowledge_base.search(
            query=search_query, num_documents=100, filters=[{"type": "stall"}]
        )
        for doc in documents:
            logger.debug("Document: %s", doc.to_dict())

        stalls_json = [doc.content for doc in documents]
        logger.debug("Found %d stalls in the knowledge base", len(stalls_json))
        return json.dumps(stalls_json)

    # def get_products_from_knowledge_base_by_category(self, category: str) -> str:
    #     """
    #     Get the list of products stored in the knowledge base for a given category.

    #     Returns:
    #         str: JSON string of products
    #     """
    #     logger.debug("Getting products from knowledge base by category: %s", category)

    #     search_filters = [
    #         {"type": "product"},
    #         {"categories": [category]},
    #     ]

    #     documents = self.knowledge_base.search(
    #         query="",
    #         num_documents=100,
    #         filters=search_filters,
    #     )

    #     logger.debug("Found %d documents with category %s", len(documents), category)
    #     for doc in documents:
    #         logger.debug("Document: %s", doc.to_dict())

    #     products_json = [doc.content for doc in documents]
    #     return json.dumps(products_json)

    def listen_for_message(self, timeout: int = 5) -> str:
        """
        Listens for incoming messages from the Nostr relay.
        Returns one message in JSON format.

        Args:
            timeout: timeout for the listen operation

        Returns:
            str: JSON string
            {
                "type": "payment request", "payment verification", "unknown",
                "kind": "kind:4", "kind:14", "none",
                "seller": "<seller bech32 public key>", "none",
                "content": "<order content>"
            }


        Raises:
            RuntimeError: if unable to listen for private messages
        """
        try:
            message = self._nostr_client.receive_message(timeout)
            message_dict = json.loads(message)
            message_kind = message_dict.get("type")
            if message_kind in {"kind:4", "kind:14"}:
                if self._message_is_payment_request(message_dict.get("content")):
                    return json.dumps(
                        {
                            "type": "payment request",
                            "seller": message_dict.get("sender"),
                            "content": message_dict.get("content"),
                        }
                    )
                if self._message_is_payment_verification(message_dict.get("content")):
                    return json.dumps(
                        {
                            "type": "payment verification",
                            "seller": message_dict.get("sender"),
                            "content": message_dict.get("content"),
                        }
                    )
            return json.dumps(
                {
                    "type": "unknown",
                    "kind": message_kind,
                    "buyer": "none",
                    "content": f"No orders received after {timeout} seconds",
                }
            )
        except RuntimeError as e:
            logger.error("Unable to listen for messages. Error %s", e)
            raise e

    def set_profile(self, profile: Profile) -> str:
        """
        Set the Nostr profile of the buyer agent.

        Args:
            profile: Nostr profile to set

        Returns:
            str: Nostr profile json string
        """
        self.profile = profile
        try:
            self._nostr_client.set_profile(profile)
        except (RuntimeError, ValueError) as e:
            logger.error("Error setting profile: %s", e)
            return json.dumps({"status": "error", "message": str(e)})

        return json.dumps({"status": "success"})

    def submit_order(self, product_name: str, quantity: int) -> str:
        """
        Purchase a product.

        TBD: Complete flow. Today it just sends first message
        and returns a fixed response.

        Args:
            product_name: name of the product to purchase
            quantity: quantity of the product to purchase

        Returns:
            str: JSON string with status and message
        """

        try:
            product = self._get_product_from_kb(product_name)
        except RuntimeError as e:
            logger.error("Error getting product from knowledge base: %s", e)
            return json.dumps({"status": "error", "message": str(e)})

        # Confirm seller has valid NIP-05
        merchant = self._nostr_client.get_profile(product.get_seller())
        if not merchant.is_nip05_validated():
            logger.error(
                "Merchant %s does not have a verified NIP-05", product.get_seller()
            )
            return json.dumps(
                {
                    "status": "error",
                    "message": "Merchant does not have a verified NIP-05",
                }
            )

        # Choosing the first shipping zone for now
        # Address is hardcoded for now. Add it to the buyer profile later.
        order_msg = self._create_customer_order(
            product.id,
            quantity,
            product.shipping[0].get_id(),
            "123 Main St, Anytown, USA",
        )

        self._nostr_client.send_message(
            "kind:14",
            product.get_seller(),
            order_msg,
        )

        return json.dumps(
            {
                "status": "success",
                "message": f"Order placed for {quantity} units of {product_name}",
                "seller": product.get_seller(),
            }
        )

    def submit_payment(self, payment_request: str) -> str:
        """
        Submit a payment to the seller.
        TBD: Complete flow. Today it just returns a fixed response.

        Args:
            payment_request: payment request to submit

        Returns:
            str: JSON string with status and message
        """

        return json.dumps(
            {
                "status": "success",
                "message": "Payment submitted",
            }
        )

    def _create_customer_order(
        self,
        product_id: str,
        quantity: int,
        shipping_id: str,
        address: Optional[str] = None,
    ) -> str:
        # Use secrets module for cryptographically secure random number generation
        random_order_id = secrets.randbelow(
            1000000000
        )  # Generate a number between 0 and 999999999
        customer_order_id_str = f"{random_order_id:09d}"

        customer_order = {
            "id": customer_order_id_str,
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
            customer_order, indent=2
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

    def _message_is_payment_request(self, message: str) -> bool:
        """
        Check if a message is a payment request.
        Args:
            message: message to check

        Returns:
            bool: True if the message is a payment request, False otherwise

        Raises:
            json.JSONDecodeError: if the message is not a valid JSON string
        """
        try:
            # Check if message is already a dictionary
            if isinstance(message, dict):
                content = message
            else:
                content = json.loads(message)

            logger.debug("_message_is_payment_request: content: %s", content)

            if content.get("type") != 1:
                return False

            payment_options = content.get("payment_options", [])
            if isinstance(payment_options, list) and any(
                isinstance(payment_option, dict)
                and "type" in payment_option
                and "link" in payment_option
                for payment_option in payment_options
            ):
                return True
            return False
        except json.JSONDecodeError:
            return False

    def _message_is_payment_verification(self, message: str) -> bool:
        """
        Check if a message is a payment verification.
        Args:
            message: message to check

        Returns:
            bool: True if the message is a payment verification, False otherwise

        Raises:
            json.JSONDecodeError: if the message is not a valid JSON string
        """
        try:
            # Check if message is already a dictionary
            if isinstance(message, dict):
                content = message
            else:
                content = json.loads(message)

            logger.debug("_message_is_payment_verification: content: %s", content)

            if content.get("type") != 2:
                return False

            paid = content.get("paid")
            shipped = content.get("shipped")

            if isinstance(paid, bool) and isinstance(shipped, bool):
                return True
            return False

        except json.JSONDecodeError:
            return False

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
            meta_data={"type": "merchant"},
        )

        # Store response
        self.knowledge_base.load_document(document=doc, filters=[{"type": "merchant"}])

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
