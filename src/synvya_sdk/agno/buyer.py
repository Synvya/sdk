"""
Module implementing the BuyerTools Toolkit for Agno agents.
"""

import json
import logging
import re
import secrets
from sys import stdout
from typing import List, Optional, Union

from pydantic import ConfigDict

from synvya_sdk import (
    Namespace,
    NostrClient,
    Product,
    Profile,
    ProfileFilter,
    ProfileType,
    Stall,
)

try:
    from agno.agent import AgentKnowledge  # type: ignore
    from agno.document.base import Document
    from agno.tools import Toolkit
    from agno.utils.log import logger
except ImportError as exc:
    raise ImportError(
        "`agno` not installed. Please install using `pip install agno`"
    ) from exc

# Create a direct console logger that doesn't rely on agno's logger
buyer_logger = logging.getLogger("synvya_buyer")
buyer_logger.setLevel(logging.INFO)
if not buyer_logger.handlers:
    handler = logging.StreamHandler(stdout)
    handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    buyer_logger.addHandler(handler)


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

    _instances_from_create: set[int] = set()
    merchants: set[Profile]

    def __init__(
        self,
        knowledge_base: AgentKnowledge,
        relays: Union[str, List[str]],
        private_key: str,
        _from_create: bool = False,
    ) -> None:
        """
        Initialize the BuyerTools object.

        Args:
            knowledge_base: Knowledge base to store and retrieve information
            relays: Nostr relay(s) that the client will connect to. Can be a single URL string or a list of URLs.
            private_key: Private key for the client in hex or bech32 format
            _from_create: Internal flag to ensure proper initialization flow
        """
        if not _from_create:
            raise RuntimeError("BuyerTools must be created using the create() method")

        # Track instance ID
        self._instance_id = id(self)
        BuyerTools._instances_from_create.add(self._instance_id)

        super().__init__(name="buyer")

        # Set include_tools to None to allow all tools to be registered
        self.include_tools = None

        # Convert single relay to list for consistent handling
        self.relays: List[str] = [relays] if isinstance(relays, str) else relays
        self.private_key: str = private_key
        self.knowledge_base: AgentKnowledge = knowledge_base
        self.profile: Optional[Profile] = None
        self._nostr_client: Optional[NostrClient] = None
        BuyerTools.merchants = set()

        # Register methods
        self.register(self.async_get_merchants)
        self.register(self.get_merchants_from_knowledge_base)
        self.register(self.async_get_merchants_in_marketplace)
        self.register(self.async_get_products)
        self.register(self.get_products_from_knowledge_base)
        # self.register(self.get_products_from_knowledge_base_by_category)
        self.register(self.get_profile)
        self.register(self.get_relay)
        self.register(self.async_get_stalls)
        self.register(self.get_stalls_from_knowledge_base)
        self.register(self.async_listen_for_message)
        self.register(self.async_submit_order)
        self.register(self.async_submit_payment)

    def __del__(self) -> None:
        """
        Delete the BuyerTools instance.
        """
        if hasattr(self, "_instance_id"):
            BuyerTools._instances_from_create.discard(self._instance_id)

    @classmethod
    async def create(
        cls,
        knowledge_base: AgentKnowledge,
        relays: Union[str, List[str]],
        private_key: str,
        log_level: Optional[int] = logging.INFO,
    ) -> "BuyerTools":
        """
        Create a new BuyerTools instance

        Args:
            knowledge_base: Knowledge base to store and retrieve information
            relays: Nostr relay(s) that the client will connect to. Can be a single URL string or a list of URLs.
            private_key: Private key for the client in hex or bech32 format
            log_level: Optional logging level

        Returns:
            BuyerTools: An initialized BuyerTools instance
        """
        instance = cls(knowledge_base, relays, private_key, _from_create=True)

        # Set logging level
        if log_level is not None:
            buyer_logger.setLevel(log_level)
            NostrClient.set_logging_level(
                log_level
            )  # Set the class-level logger BEFORE creating any instances
        else:
            buyer_logger.setLevel(logger.getEffectiveLevel())
            NostrClient.set_logging_level(logger.getEffectiveLevel())

        # Then initialize NostrClient with proper logging already set up
        instance._nostr_client = await NostrClient.create(relays, private_key)

        instance.profile = await instance._nostr_client.async_get_profile()

        return instance

    async def async_get_merchants(
        self, profile_filter_json: Optional[str | dict] = None
    ) -> str:
        """
        Download from the Nostr relay all merchants and store their Nostr
        profile in the knowledge base.

        Args:
            profile_filter_json: JSON string or dictionary representing a filter to apply to merchants.
                                Format: {"namespace": "MERCHANT", "profile_type": "restaurant", "hashtags": ["pizza"]}

        Returns:
            str: JSON string with status and count of merchants refreshed
        """
        buyer_logger.debug(
            "GET_MERCHANTS: profile_filter_json: %s", profile_filter_json
        )

        # If there is no filter, get all merchants
        if profile_filter_json is None:
            try:
                self.merchants = await self._nostr_client.async_get_merchants()
            except RuntimeError as e:
                logger.error("Error downloading merchants from the Nostr relay: %s", e)
                return json.dumps({"status": "error", "message": str(e)})

            # Store merchants in knowledge base
            for merchant in self.merchants:
                self._store_profile_in_kb(merchant)

            response = json.dumps({"status": "success", "count": len(self.merchants)})
            buyer_logger.debug("GET_MERCHANTS: response: %s", response)
            return response

        # If there is a filter, get the merchants that match the filter
        filter_data = None
        if isinstance(profile_filter_json, str):
            # Parse the JSON string into a dict
            filter_data = json.loads(profile_filter_json)
        elif isinstance(profile_filter_json, dict):
            # Use the dictionary directly
            filter_data = profile_filter_json

        # Extract the values
        namespace_str = filter_data.get("namespace")
        profile_type_str = filter_data.get("profile_type")
        hashtags = filter_data.get("hashtags", [])

        # Convert namespace string to Namespace enum
        namespace = None
        if namespace_str:
            try:
                namespace = getattr(Namespace, namespace_str)
            except AttributeError as e:
                if namespace_str in [n.value for n in Namespace]:
                    # If the string is the value rather than the name
                    namespace = [n for n in Namespace if n.value == namespace_str][0]
                else:
                    raise ValueError(f"Invalid namespace: {namespace_str}") from e

        # Convert profile_type string to ProfileType enum
        profile_type = None
        if profile_type_str:
            # Try to match by direct enum name first
            try:
                profile_type = getattr(
                    ProfileType, f"MERCHANT_{profile_type_str.upper()}"
                )
            except AttributeError as e:
                # Try to match by enum value
                matching_types = [
                    pt for pt in ProfileType if pt.value == profile_type_str
                ]
                if matching_types:
                    profile_type = matching_types[0]
                else:
                    raise ValueError(
                        f"Invalid profile_type: {profile_type_str}. "
                        f"Valid values are: {[pt.value for pt in ProfileType]}"
                    ) from e

        # Create the ProfileFilter
        profile_filter = ProfileFilter(
            namespace=namespace,
            profile_type=profile_type,
            hashtags=hashtags,
        )
        buyer_logger.debug("Created ProfileFilter: %s", profile_filter)

        # Get the merchants that match the filter
        try:
            self.merchants = await self._nostr_client.async_get_merchants(
                profile_filter
            )
        except RuntimeError as e:
            buyer_logger.error(
                "Error downloading merchants from the Nostr relay: %s", e
            )
            return json.dumps({"status": "error", "message": str(e)})

        # Store merchants in knowledge base
        for merchant in self.merchants:
            self._store_profile_in_kb(merchant)

        response = json.dumps({"status": "success", "count": len(self.merchants)})
        buyer_logger.debug("GET_MERCHANTS: response: %s", response)

        return response

    def get_merchants_from_knowledge_base(
        self, profile_filter_json: Optional[str | dict] = None
    ) -> str:
        """
        Get the list of merchants stored in the knowledge base.

        Args:
            profile_filter_json: JSON string or dictionary representing a filter to apply to merchants.
                             Format: {"namespace": "com.synvya.merchant", "profile_type": "restaurant", "hashtags": ["pizza"]}

        Returns:
            str: JSON string of merchants
        """
        buyer_logger.debug(
            "GET_MERCHANTS_FROM_KNOWLEDGE_BASE: profile_filter_json: %s",
            str(profile_filter_json),
        )

        # Initialize filter list
        search_filters = []

        # Process profile filter if provided
        if profile_filter_json:
            try:
                # Parse filter data
                filter_data = (
                    json.loads(profile_filter_json)
                    if isinstance(profile_filter_json, str)
                    else profile_filter_json
                )

                # Add namespace filter (exact match)
                namespace = filter_data.get("namespace")
                if namespace:
                    search_filters.append({"namespace": namespace})

                # Add profile_type filter (exact match)
                profile_type = filter_data.get("profile_type")
                if profile_type:
                    search_filters.append({"profile_type": profile_type})

                # Add hashtag filters (boolean match per hashtag)
                hashtags = filter_data.get("hashtags", [])
                for tag in hashtags:
                    normalized_tag = self._normalize_hashtag(tag)
                    search_filters.append({f"hashtag_{normalized_tag}": True})

                buyer_logger.debug("Applied search filters: %s", search_filters)

            except json.JSONDecodeError as e:
                buyer_logger.error("Invalid JSON format for profile_filter: %s", e)
                return json.dumps(
                    {"status": "error", "message": f"Invalid JSON format: {str(e)}"}
                )
            except Exception as e:
                buyer_logger.error("Error processing profile filter: %s", e)
                return json.dumps(
                    {"status": "error", "message": f"Error processing filter: {str(e)}"}
                )

        buyer_logger.debug("Search filters: %s", str(search_filters))

        # Execute search
        documents = self.knowledge_base.search(
            query="", num_documents=100, filters=search_filters
        )

        buyer_logger.debug("Found %d merchants in the knowledge base", len(documents))

        # Return JSON content of found merchants
        merchants_json = [doc.content for doc in documents]
        buyer_logger.debug("Merchants JSON: %s", str(merchants_json))
        return json.dumps(merchants_json)

    async def async_get_merchants_in_marketplace(
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
        buyer_logger.debug("Downloading merchants from the Nostr marketplace %s", name)
        try:
            # Retrieve merchants from the Nostr marketplace
            self.merchants = (
                await self._nostr_client.async_get_merchants_in_marketplace(
                    owner_public_key, name, profile_filter
                )
            )
            # Store merchants in the knowledge base
            for merchant in self.merchants:
                self._store_profile_in_kb(merchant)

            # Return the number of merchants downloaded
            response = json.dumps({"status": "success", "count": len(self.merchants)})
        except RuntimeError as e:
            buyer_logger.error(
                "Error downloading merchants from the Nostr marketplace %s: %s",
                name,
                e,
            )
            response = json.dumps({"status": "error", "message": str(e)})

        return response

    async def async_get_products(
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
        buyer_logger.debug("Downloading products from merchant %s", merchant_public_key)
        try:
            # retrieve products from the Nostr relay
            products = await self._nostr_client.async_get_products(
                merchant_public_key, stall
            )

            # store products in the knowledge base
            for product in products:
                self._store_product_in_kb(product)

            response = json.dumps([product.to_dict() for product in products])

        except RuntimeError as e:
            buyer_logger.error(
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
        buyer_logger.debug("Getting products from knowledge base")

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
            buyer_logger.debug("Document: %s", doc.to_dict())

        products_json = [doc.content for doc in documents]
        buyer_logger.debug(
            "Found %d products in the knowledge base", len(products_json)
        )
        return json.dumps(products_json)

    def get_profile(self) -> str:
        """
        Get the Nostr profile of the buyer agent.

        Returns:
            str: buyer profile json string
        """
        buyer_logger.debug("Getting own profile")
        return self.profile.to_json()

    def get_relay(self) -> str:
        """Get the Nostr relay that the buyer agent is using.

        Returns:
            str: Primary Nostr relay (first in the list)
        """
        return self.relays[0] if self.relays else ""

    def get_relays(self) -> List[str]:
        """Get all Nostr relays that the buyer agent is using.

        Returns:
            List[str]: List of Nostr relays
        """
        return self.relays

    async def async_get_stalls(self, merchant_public_key: str) -> str:
        """
        Download all stalls published by a merchant on Nostr and store them
        in the knowledge base.

        Args:
            merchant_public_key: public key of the merchant

        Returns:
            str: JSON string with all stalls published by the merchant
        """
        buyer_logger.debug("Downloading stalls from merchant %s", merchant_public_key)
        try:
            # retrieve stalls from the Nostr relay
            stalls = await self._nostr_client.async_get_stalls(merchant_public_key)

            # store stalls in the knowledge base
            for stall in stalls:
                self._store_stall_in_kb(stall)

            # convert stalls to JSON string
            response = json.dumps([stall.to_dict() for stall in stalls])
        except RuntimeError as e:
            buyer_logger.error(
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
        buyer_logger.debug("Getting stalls from knowledge base")

        if merchant_public_key is not None:
            search_query = merchant_public_key
        else:
            search_query = ""

        documents = self.knowledge_base.search(
            query=search_query, num_documents=100, filters=[{"type": "stall"}]
        )
        for doc in documents:
            buyer_logger.debug("Document: %s", doc.to_dict())

        stalls_json = [doc.content for doc in documents]
        buyer_logger.debug("Found %d stalls in the knowledge base", len(stalls_json))
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

    async def async_listen_for_message(self, timeout: int = 5) -> str:
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
            message = await self._nostr_client.async_receive_message(timeout)
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
            buyer_logger.error("Unable to listen for messages. Error %s", e)
            raise e

    async def async_set_profile(self, profile: Profile) -> str:
        """
        Set the Nostr profile of the buyer agent.

        Args:
            profile: Nostr profile to set

        Returns:
            str: Nostr profile json string
        """
        self.profile = profile
        try:
            await self._nostr_client.async_set_profile(profile)
        except (RuntimeError, ValueError) as e:
            buyer_logger.error("Error setting profile: %s", e)
            return json.dumps({"status": "error", "message": str(e)})

        return json.dumps({"status": "success"})

    async def async_submit_order(self, product_name: str, quantity: int) -> str:
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
            buyer_logger.error("Error getting product from knowledge base: %s", e)
            return json.dumps({"status": "error", "message": str(e)})

        if not product.get_seller():
            buyer_logger.error("Product %s has no seller", product_name)
            return json.dumps({"status": "error", "message": "Product has no seller"})

        try:
            # Confirm seller has valid NIP-05
            merchant = await self._nostr_client.async_get_profile(product.get_seller())
            if not merchant.is_nip05_validated():
                buyer_logger.error(
                    "Merchant %s does not have a verified NIP-05", product.get_seller()
                )
                return json.dumps(
                    {
                        "status": "error",
                        "message": "Merchant does not have a verified NIP-05",
                    }
                )
        except (ValueError, RuntimeError) as e:
            buyer_logger.error("Error retrieving seller profile: %s", e)
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Unable to retrieve seller profile for {product.get_seller()}: {str(e)}",
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

        await self._nostr_client.async_send_message(
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

    async def async_submit_payment(self, payment_request: str) -> str:
        """
        Submit a payment to the seller.
        TBD: Complete flow. Today it just returns a fixed response.

        Args:
            payment_request: payment request to submit

        Returns:
            str: JSON string with status and message
        """
        buyer_logger.debug("Submitting payment: %s", payment_request)

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
        buyer_logger.debug("Getting product from knowledge base: %s", product_name)
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

            buyer_logger.debug("_message_is_payment_request: content: %s", content)

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

            buyer_logger.debug("_message_is_payment_verification: content: %s", content)

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
        buyer_logger.debug("_store_profile_in_kb: profile: %s", profile.get_name())

        profile_type_str = profile.get_profile_type().value

        doc = Document(
            content=profile.to_json(),
            name=profile.get_name(),
            meta_data={
                "type": "merchant",
                "public_key": profile.get_public_key(),
            },
        )

        hashtags = profile.get_hashtags()
        hashtag_filters = [
            {f"hashtag_{self._normalize_hashtag(tag)}": True} for tag in hashtags
        ]

        filters = [
            {"namespace": profile.get_namespace()},
            {"profile_type": profile_type_str},
            *hashtag_filters,
        ]
        buyer_logger.debug("_store_profile_in_kb: filters: %s", filters)
        self.knowledge_base.load_document(
            document=doc,
            filters=filters,
        )

    def _store_product_in_kb(self, product: Product) -> None:
        """
        Store a Nostr product in the knowledge base.

        Args:
            product: Nostr product to store
        """
        buyer_logger.debug("Storing product in knowledge base: %s", product.name)

        doc = Document(
            content=product.to_json(),
            name=product.name,
            meta_data={"type": "product"},
        )

        # Store response
        self.knowledge_base.load_documents(
            documents=[doc],
            filters=[{"type": "product"}, {"categories": product.categories}],
        )

    def _store_stall_in_kb(self, stall: Stall) -> None:
        """
        Store a Nostr stall in the knowledge base.

        Args:
            stall: Nostr stall to store
        """
        buyer_logger.debug("Storing stall in knowledge base: %s", stall.name)

        doc = Document(
            content=stall.to_json(),
            name=stall.name,
            meta_data={"type": "stall"},
        )

        # Store response
        self.knowledge_base.load_documents(documents=[doc], filters=[{"type": "stall"}])

    @staticmethod
    def _normalize_hashtag(tag: str) -> str:
        """
        Normalize hashtags by removing spaces, underscores, and hyphens,
        and converting to lowercase.
        Ensures consistent matching across variations.
        """
        tag = tag.lower()
        tag = re.sub(r"[\s\-_]+", "", tag)  # Remove spaces, hyphens, underscores
        return tag
