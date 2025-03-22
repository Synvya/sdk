"""
Module implementing the MerchantTools Toolkit for Agno agents.
"""

import json
import time
from typing import List, Optional, Tuple

from nostr_sdk import EventId
from pydantic import ConfigDict

from synvya_sdk import NostrClient, Product, Profile, Stall

try:
    from agno.tools import Toolkit
    from agno.utils.log import logger
except ImportError as exc:
    raise ImportError(
        "`agno` not installed. Please install using `pip install agno`"
    ) from exc


class MerchantTools(Toolkit):
    """
    MerchantTools is a toolkit that allows a merchant to publish
    products and stalls to Nostr.

    TBD:
    - At initialization, products and stalls are added to the internal database
    but not published to Nostr. User must call publish_products() and
    publish_stalls() to publish the products and stalls to Nostr.

    After the initial publication, the user can call get_products() and
    get_stalls() to get the current products and stalls in the internal database, update
    the products or stalls, and then call set_products() and set_stalls() to
    update the internal database and simultaneously publish the changes to Nostr.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, extra="allow", validate_assignment=True
    )

    _nostr_client: Optional[NostrClient] = None
    product_db: List[Tuple[Product, Optional[EventId]]] = []
    stall_db: List[Tuple[Stall, Optional[EventId]]] = []

    def __init__(
        self,
        relay: str,
        private_key: str,
        stalls: List[Stall],
        products: List[Product],
    ):
        """Initialize the Merchant toolkit.

        Args:
            relay: Nostr relay to use for communications
            private_key: private key of the merchant using this agent
            stalls: list of stalls managed by this merchant
            products: list of products sold by this merchant
        """
        super().__init__(name="merchant")
        self.relay = relay
        self.private_key = private_key
        self._nostr_client = NostrClient(relay, private_key)
        self._nostr_client.set_logging_level(logger.getEffectiveLevel())

        self.profile = self._nostr_client.get_profile()

        # initialize the Product DB with no event id
        self.product_db = [(product, None) for product in products]

        # initialize the Stall DB with no event id
        self.stall_db = [(stall, None) for stall in stalls]

        # Register methods
        self.register(self.get_profile)
        self.register(self.get_products)
        self.register(self.get_relay)
        self.register(self.get_stalls)
        self.register(self.listen_for_orders)
        self.register(self.manual_order_workflow)
        self.register(self.process_order)
        self.register(self.publish_product)
        self.register(self.publish_products)
        self.register(self.publish_stall)
        self.register(self.publish_stalls)
        self.register(self.set_products)
        self.register(self.set_profile)
        self.register(self.set_stalls)
        self.register(self.remove_products)
        self.register(self.remove_stalls)

    def get_profile(self) -> str:
        """
        Get the merchant profile in JSON format

        Returns:
            str: merchant profile in JSON format
        """
        return json.dumps(self.profile.to_json())

    def get_products(self) -> str:
        """
        Get all the merchant products

        Returns:
            str: JSON string containing all products
        """
        return json.dumps([p.to_dict() for p, _ in self.product_db])

    def get_relay(self) -> str:
        """
        Get the Nostr relay the merchant is using

        Returns:
            str: Nostr relay
        """
        return self.relay

    def get_stalls(self) -> str:
        """
        Get all the merchant stalls in JSON format

        Returns:
            str: JSON string containing all stalls
        """
        return json.dumps([s.to_dict() for s, _ in self.stall_db])

    def listen_for_orders(self) -> str:
        """
        Listens for orders to be processed by the Nostr relay

        Returns:
            str: JSON string of the content of the private message or an error message

        Raises:
            RuntimeError: if unable to listen for private messages
        """
        try:
            order = self._nostr_client.receive_message()
            logger.info("Received order: %s", order)
            return json.dumps(order)
        except RuntimeError as e:
            logger.error("Unable to listen for messages. Error %s", e)
            raise e

    def manual_order_workflow(self, order: str, parameters: str) -> str:
        """
        Placeholder for a manual order workflow

        Args:
            order: JSON string of the order
            parameters: JSON string of the parameters

        Returns:
            str: JSON string of the payment request
        """
        return json.dumps(
            {
                "status": "success",
                "message": f"Workflow triggered for order: {order} with parameters: {parameters}",
            }
        )

    def process_order(self, order: str, payment_type: str, payment_url: str) -> str:
        """
        Processes an order

        Args:
            order: JSON string of the order
            payment_type: Type of payment
            payment_url: URL of the payment

        Returns:
            str: JSON string of the payment request
        """
        try:
            order_dict = json.loads(order)
        except json.JSONDecodeError:
            return json.dumps({"status": "error", "message": "Invalid order format"})
        order_id = order_dict.get("id")

        is_valid_payment_type = payment_type in ["URL", "BTC", "LN", "LNURL"]
        if not is_valid_payment_type:
            return json.dumps({"status": "error", "message": "Invalid payment type"})

        payment_request = self._create_payment_request(
            order_id, payment_type, payment_url
        )
        return json.dumps(payment_request)

    def publish_product(self, product: Product) -> str:
        """
        Publishes to Nostr a single product.
        Adds the product to the Product DB if it is not already present.
        Updates the Product DB with new event id if the product is already present.

        Args:
            product: Product to be published

        Returns:
            str: JSON string with status of the operation

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            logger.error("NostrClient not initialized")
            raise ValueError("NostrClient not initialized")

        try:
            event_id = self._nostr_client.set_product(product)
            if product not in self.product_db:
                # we need to add the product event id to the product db
                self.product_db.append((product, event_id))
            else:
                # we need to update the product event id in the product db
                self.product_db[self.product_db.index((product, None))] = (
                    product,
                    event_id,
                )
            logger.debug(
                f"Published product {product.name} with categories {', '.join(product.categories)}"
            )
            return json.dumps(
                {
                    "status": "success",
                    "event_id": str(event_id),
                    "product_name": product.name,
                }
            )
        except RuntimeError as e:
            logger.error("Unable to publish product %s. Error %s", product, e)
            return json.dumps(
                {"status": "error", "message": str(e), "product_name": product.name}
            )

    def publish_products(
        self,
        stall: Optional[Stall] = None,
        products: Optional[List[Product]] = None,
    ) -> str:
        """
        Publishes to Nostr all products in the Merchant's Product DB
        Optional parameters can be used to publish only a subset of the Product DB

        Args:
            stall: Optional publish all products for a given stall
            products: Optional subset of products to publish

        Returns:
            str: JSON array with status of all product publishing operations

        Raises:
            ValueError: if NostrClient is not initialized
        """

        if self._nostr_client is None:
            logger.error("NostrClient not initialized")
            raise ValueError("NostrClient not initialized")

        results = []

        for i, (product, _) in enumerate(self.product_db):
            if stall is not None and product.stall_id != stall.id:
                continue
            if products is not None and product not in products:
                continue
            try:
                event_id = self._nostr_client.set_product(product)
                logger.debug(
                    f"Published product {product.name} with categories {', '.join(product.categories)}"
                )
                self.product_db[i] = (product, event_id)
                results.append(
                    {
                        "status": "success",
                        "event_id": str(event_id),
                        "product_name": product.name,
                    }
                )
                # Pause for 0.5 seconds to avoid rate limiting
                time.sleep(0.5)
            except RuntimeError as e:
                logger.error("Unable to publish product %s. Error %s", product, e)
                results.append(
                    {"status": "error", "message": str(e), "product_name": product.name}
                )

        return json.dumps(results)

    def publish_stall(self, stall: Stall) -> str:
        """
        Publishes to Nostr a single stall.
        Adds the stall to the Stall DB if it is not already present.
        Updates the Stall DB with new event id if the stall is already present.

        Does NOT publish the products for the stall.
        Call publish_products() to publish the products for the stall.

        Args:
            stall: Stall to be published

        Returns:
            str: JSON string with status of the operation

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            logger.error("NostrClient not initialized")
            raise ValueError("NostrClient not initialized")

        try:
            event_id = self._nostr_client.set_stall(stall)
            if stall not in self.stall_db:
                # we need to add the stall event id to the stall db
                self.stall_db.append((stall, event_id))
            else:
                # we need to update the stall event id in the stall db
                self.stall_db[self.stall_db.index((stall, None))] = (stall, event_id)
            return json.dumps(
                {
                    "status": "success",
                    "event_id": str(event_id),
                    "stall_name": stall.name,
                }
            )
        except RuntimeError as e:
            logger.error("Unable to publish the stall: %s", e)
            return json.dumps(
                {"status": "error", "message": str(e), "stall_name": stall.name}
            )

    def publish_stalls(
        self,
        stalls: Optional[List[Stall]] = None,
    ) -> str:
        """
        Publishes to Nostr all stalls managed by the merchant
        Optional parameters can be used to publish only a subset of the Stall DB

        Args:
            stalls: Optional subset of stalls to publish

        Returns:
            str: JSON array with status of all stall publishing operations

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            logger.error("NostrClient not initialized")
            raise ValueError("NostrClient not initialized")

        results = []

        for i, (stall, _) in enumerate(self.stall_db):
            if stalls is not None and stall not in stalls:
                continue
            try:
                event_id = self._nostr_client.set_stall(stall)
                self.stall_db[i] = (stall, event_id)
                results.append(
                    {
                        "status": "success",
                        "event_id": str(event_id),
                        "stall_name": stall.name,
                    }
                )
                # Pause for 0.5 seconds to avoid rate limiting
                time.sleep(0.5)
            except RuntimeError as e:
                logger.error("Unable to publish stall %s. Error %s", stall, e)
                results.append(
                    {"status": "error", "message": str(e), "stall_name": stall.name}
                )

        return json.dumps(results)

    # def publish_product_by_name(self, arguments: str) -> str:
    #     """
    #     Publishes or updates to Nostra given product from the Merchant's Product DB
    #     Args:
    #         arguments: JSON string that may contain
    #         {"name": "product_name"} or just "product_name"

    #     Returns:
    #         str: JSON string with status of the operation

    #     Raises:
    #         ValueError: if NostrClient is not initialized
    #     """
    #     if self._nostr_client is None:
    #         logger.error("NostrClient not initialized")
    #         raise ValueError("NostrClient not initialized")

    #     try:
    #         # Try to parse as JSON first
    #         if isinstance(arguments, dict):
    #             parsed = arguments
    #         else:
    #             parsed = json.loads(arguments)
    #         name = parsed.get(
    #             "name", parsed
    #         )  # Get name if exists, otherwise use whole value
    #     except json.JSONDecodeError:
    #         # If not JSON, use the raw string
    #         name = arguments

    #     # iterate through all products searching for the right name
    #     for i, (product, _) in enumerate(self.product_db):
    #         if product.name == name:
    #             try:
    #                 # Convert MerchantProduct to ProductData for nostr_client
    #                 # product_data = product.to_product_data()
    #                 # Publish using the SDK's synchronous method
    #                 event_id = self._nostr_client.publish_product(product)
    #                 # Update the product_db with the new event_id
    #                 self.product_db[i] = (product, event_id)
    #                 # Pause for 0.5 seconds to avoid rate limiting
    #                 time.sleep(0.5)
    #                 return json.dumps(
    #                     {
    #                         "status": "success",
    #                         "event_id": str(event_id),
    #                         "product_name": product.name,
    #                     }
    #                 )
    #             except RuntimeError as e:
    #                 logger.error("Unable to publish product %s. Error %s", product, e)
    #                 return json.dumps(
    #                     {
    #                         "status": "error",
    #                         "message": str(e),
    #                         "product_name": product.name,
    #                     }
    #                 )

    #     # If we are here, then we didn't find a match
    #     return json.dumps(
    #         {
    #             "status": "error",
    #             "message": f"Product '{name}' not found in database",
    #             "product_name": name,
    #         }
    #     )

    # def publish_products_by_stall_name(self, arguments: Union[str, dict]) -> str:
    #     """
    #     Publishes or updates to Nostr all products sold by the merchant in a given stall

    #     Args:
    #         arguments: str or dict with the stall name. Can be in formats:
    #             - {"name": "stall_name"}
    #             - {"arguments": "{\"name\": \"stall_name\"}"}
    #             - "stall_name"

    #     Returns:
    #         str: JSON array with status of all product publishing operations

    #     Raises:
    #         ValueError: if NostrClient is not initialized
    #     """
    #     if self._nostr_client is None:
    #         logger.error("NostrClient not initialized")
    #         raise ValueError("NostrClient not initialized")

    #     try:
    #         # Parse arguments to get stall_name
    #         stall_name: str
    #         if isinstance(arguments, str):
    #             try:
    #                 parsed = json.loads(arguments)
    #                 if isinstance(parsed, dict):
    #                     raw_name: Optional[Any] = parsed.get("name")
    #                     stall_name = str(raw_name) if raw_name is not None else ""
    #                 else:
    #                     stall_name = arguments
    #             except json.JSONDecodeError:
    #                 stall_name = arguments
    #         else:
    #             if "arguments" in arguments:
    #                 nested = json.loads(arguments["arguments"])
    #                 if isinstance(nested, dict):
    #                     raw_name = nested.get("name")
    #                     stall_name = str(raw_name) if raw_name is not None else ""
    #                 else:
    #                     raw_name = nested
    #                     stall_name = str(raw_name) if raw_name is not None else ""
    #             else:
    #                 raw_name = arguments.get("name", arguments)
    #                 stall_name = str(raw_name) if raw_name is not None else ""

    #         results = []
    #         stall_id = None

    #         # Find stall ID
    #         for stall, _ in self.stall_db:
    #             if stall.name == stall_name:
    #                 stall_id = stall.id
    #                 break

    #         if stall_id is None:
    #             return json.dumps(
    #                 [
    #                     {
    #                         "status": "error",
    #                         "message": f"Stall '{stall_name}' not found in database",
    #                         "stall_name": stall_name,
    #                     }
    #                 ]
    #             )

    #         # Publish products
    #         for i, (product, _) in enumerate(self.product_db):
    #             if product.stall_id == stall_id:
    #                 try:
    #                     # product_data = product.to_product_data()
    #                     event_id = self._nostr_client.publish_product(product)
    #                     self.product_db[i] = (product, event_id)
    #                     results.append(
    #                         {
    #                             "status": "success",
    #                             "event_id": str(event_id),
    #                             "product_name": product.name,
    #                             "stall_name": stall_name,
    #                         }
    #                     )
    #                     # Pause for 0.5 seconds to avoid rate limiting
    #                     time.sleep(0.5)
    #                 except RuntimeError as e:
    #                     logger.error(
    #                         "Unable to publish product %s. Error %s", product, e
    #                     )
    #                     results.append(
    #                         {
    #                             "status": "error",
    #                             "message": str(e),
    #                             "product_name": product.name,
    #                             "stall_name": stall_name,
    #                         }
    #                     )

    #         if not results:
    #             logger.error("No products found in stall '%s'", stall_name)
    #             return json.dumps(
    #                 [
    #                     {
    #                         "status": "error",
    #                         "message": f"No products found in stall '{stall_name}'",
    #                         "stall_name": stall_name,
    #                     }
    #                 ]
    #             )

    #         return json.dumps(results)

    #     except RuntimeError as e:
    #         logger.error(
    #             "Unable to publish products in stall '%s'. Error %s", stall_name, e
    #         )
    #         return json.dumps(
    #             [{"status": "error", "message": str(e), "arguments": str(arguments)}]
    #         )

    def set_products(self, products: List[Product]) -> str:
        """
        Sets the products used by the Toolkit.
        The products are also published to the Nostr network.
        """
        self.product_db = [(product, None) for product in products]
        return self.publish_products()

    def set_profile(self, profile: Profile) -> str:
        """
        Sets the profile used by the Toolkit.
        The profile is also published to the Nostr network.

        Returns:
            str: id of the event publishing the profile

        Raises:
            RuntimeError: if it can't publish the event
        """
        if self._nostr_client is None:
            logger.error("NostrClient not initialized")
            raise ValueError("NostrClient not initialized")

        try:
            return self._nostr_client.set_profile(profile)
        except RuntimeError as e:
            logger.error("Unable to publish the profile: %s", e)
            raise RuntimeError(f"Unable to publish the profile: {e}") from e

    def set_stalls(self, stalls: List[Stall]) -> str:
        """
        Sets the stalls used by the Toolkit.
        The stalls are also published to the Nostr network.
        """
        self.stall_db = [(stall, None) for stall in stalls]
        return self.publish_stalls()

    # def publish_stall_by_name(self, arguments: Union[str, dict]) -> str:
    #     """
    #     Publishes or updates to Nostr a given stall by name

    #     Args:
    #         arguments: str or dict with the stall name. Can be in formats:
    #             - {"name": "stall_name"}
    #             - {"arguments": "{\"name\": \"stall_name\"}"}
    #             - "stall_name"

    #     Returns:
    #         str: JSON array with status of the operation

    #     Raises:
    #         ValueError: if NostrClient is not initialized
    #     """
    #     if self._nostr_client is None:
    #         logger.error("NostrClient not initialized")
    #         raise ValueError("NostrClient not initialized")

    #     try:
    #         # Parse arguments to get stall_name
    #         stall_name: str
    #         if isinstance(arguments, str):
    #             try:
    #                 # Try to parse as JSON first
    #                 parsed = json.loads(arguments)
    #                 if isinstance(parsed, dict):
    #                     raw_name: Optional[Any] = parsed.get("name")
    #                     stall_name = str(raw_name) if raw_name is not None else ""
    #                 else:
    #                     stall_name = arguments
    #             except json.JSONDecodeError:
    #                 # If not JSON, use the raw string
    #                 stall_name = arguments
    #         else:
    #             # Handle dict input
    #             if "arguments" in arguments:
    #                 nested = json.loads(arguments["arguments"])
    #                 if isinstance(nested, dict):
    #                     raw_name = nested.get("name")
    #                     stall_name = str(raw_name) if raw_name is not None else ""
    #                 else:
    #                     raw_name = nested
    #                     stall_name = str(raw_name) if raw_name is not None else ""
    #             else:
    #                 raw_name = arguments.get("name", arguments)
    #                 stall_name = str(raw_name) if raw_name is not None else ""

    #         # Find and publish stall
    #         for i, (stall, _) in enumerate(self.stall_db):
    #             if stall.name == stall_name:
    #                 try:
    #                     event_id = self._nostr_client.publish_stall(stall)
    #                     self.stall_db[i] = (stall, event_id)
    #                     # Pause for 0.5 seconds to avoid rate limiting
    #                     time.sleep(0.5)
    #                     return json.dumps(
    #                         {
    #                             "status": "success",
    #                             "event_id": str(event_id),
    #                             "stall_name": stall.name,
    #                         }
    #                     )

    #                 except RuntimeError as e:
    #                     logger.error("Unable to publish stall %s. Error %s", stall, e)
    #                     return json.dumps(
    #                         [
    #                             {
    #                                 "status": "error",
    #                                 "message": str(e),
    #                                 "stall_name": stall.name,
    #                             }
    #                         ]
    #                     )

    #         # Stall not found
    #         logger.error("Stall '%s' not found in database", stall_name)
    #         return json.dumps(
    #             [
    #                 {
    #                     "status": "error",
    #                     "message": f"Stall '{stall_name}' not found in database",
    #                     "stall_name": stall_name,
    #                 }
    #             ]
    #         )

    #     except RuntimeError as e:
    #         logger.error("Unable to publish stall '%s'. Error %s", stall_name, e)
    #         return json.dumps(
    #             [{"status": "error", "message": str(e), "stall_name": "unknown"}]
    #         )

    def remove_products(
        self,
        stall: Optional[Stall] = None,
        products: Optional[List[Product]] = None,
    ) -> str:
        """
        Removes from Nostr and the internal database all products published by the merchant
        Optional parameters can be used to remove only a subset of the products

        Args:
            stall: Optional remove only products for a given stall
            products: Optional subset of products to remove

        Returns:
            str: JSON array with status of all product removal operations

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            logger.error("NostrClient not initialized")
            raise ValueError("NostrClient not initialized")

        results = []

        for product, event_id in enumerate(self.product_db):
            if stall is not None and product.stall_id != stall.id:
                continue
            if products is not None and product not in products:
                continue

            if event_id is None:
                # product has not been published to Nostr
                # remove from database and call it a success
                self.product_db.remove((product, event_id))
                results.append(
                    {
                        "status": "success",
                        "message": f"Product '{product.name}' removed",
                        "product_name": product.name,
                        "event_id": "not previously published",
                    }
                )

                continue

            try:
                # product has been published to Nostr
                # delete the event from Nostr
                # remove from database and call it a success

                delete_event_id = self._nostr_client.delete_event(
                    event_id, reason=f"Product '{product.name}' removed"
                )
                self.product_db.remove((product, event_id))
                results.append(
                    {
                        "status": "success",
                        "message": f"Product '{product.name}' removed",
                        "product_name": product.name,
                        "event_id": str(delete_event_id),
                    }
                )
                # Pause for 0.5 seconds to avoid rate limiting
                time.sleep(0.5)
            except RuntimeError as e:
                logger.error("Unable to remove product %s. Error %s", product, e)
                results.append(
                    {"status": "error", "message": str(e), "product_name": product.name}
                )

        return json.dumps(results)

    def remove_stalls(
        self,
        stalls: Optional[List[Stall]] = None,
    ) -> str:
        """
        Removes from Nostr and the internal database all stalls managed by the merchant
        Optional parameters can be used to remove only a subset of the stalls

        Does ALSO remove all products within the stalls.

        Args:
            stalls: Optional subset of stalls to remove

        Returns:
            str: JSON array with status of all removal operations

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            logger.error("NostrClient not initialized")
            raise ValueError("NostrClient not initialized")

        results = []

        for stall, event_id in self.stall_db:
            if stalls is not None and stall not in stalls:
                continue  # we're filtering out the stalls that are not in the list

            # remove all products in this stall
            results.extend(self.remove_products(products=None, stall=stall))

            # now remove the stall
            try:
                delete_event_id = self._nostr_client.delete_event(
                    stall.id, reason=f"Stall '{stall.name}' removed"
                )
                self.stall_db.remove((stall, event_id))
                results.append(
                    {
                        "status": "success",
                        "message": f"Stall '{stall.name}' removed",
                        "stall_name": stall.name,
                        "event_id": str(delete_event_id),
                    }
                )

                # Pause for 0.5 seconds to avoid rate limiting
                time.sleep(0.5)
            except RuntimeError as e:
                logger.error("Unable to remove stall %s. Error %s", stall.name, e)
                results.append(
                    {"status": "error", "message": str(e), "stall_name": stall.name}
                )

        return json.dumps(results)

    # def remove_product_by_name(self, arguments: str) -> str:
    #     """
    #     Removes from Nostr a product with the given name

    #     Args:
    #         arguments: JSON string that may contain {"name": "product_name"}
    #         or just "product_name"

    #     Returns:
    #         str: JSON string with status of the operation

    #     Raises:
    #         ValueError: if NostrClient is not initialized
    #     """
    #     if self._nostr_client is None:
    #         logger.error("NostrClient not initialized")
    #         raise ValueError("NostrClient not initialized")

    #     try:
    #         # Try to parse as JSON first
    #         if isinstance(arguments, dict):
    #             parsed = arguments
    #         else:
    #             parsed = json.loads(arguments)
    #         name = parsed.get(
    #             "name", parsed
    #         )  # Get name if exists, otherwise use whole value
    #     except json.JSONDecodeError:
    #         # If not JSON, use the raw string
    #         name = arguments

    #     # Find the product and its event_id in the product_db
    #     for i, (product, event_id) in enumerate(self.product_db):
    #         if product.name == name:
    #             if event_id is None:
    #                 return json.dumps(
    #                     {
    #                         "status": "error",
    #                         "message": f"Product '{name}' has not been published yet",
    #                         "product_name": name,
    #                     }
    #                 )

    #             try:
    #                 # Delete the event using the SDK's method
    #                 self._nostr_client.delete_event(
    #                     event_id, reason=f"Product '{name}' removed"
    #                 )
    #                 # Remove the event_id, keeping the product in the database
    #                 self.product_db[i] = (product, None)
    #                 # Pause for 0.5 seconds to avoid rate limiting
    #                 time.sleep(0.5)
    #                 return json.dumps(
    #                     {
    #                         "status": "success",
    #                         "message": f"Product '{name}' removed",
    #                         "product_name": name,
    #                         "event_id": str(event_id),
    #                     }
    #                 )
    #             except RuntimeError as e:
    #                 logger.error("Unable to remove product %s. Error %s", name, e)
    #                 return json.dumps(
    #                     {"status": "error", "message": str(e), "product_name": name}
    #                 )

    #     # If we get here, we didn't find the product
    #     return json.dumps(
    #         {
    #             "status": "error",
    #             "message": f"Product '{name}' not found in database",
    #             "product_name": name,
    #         }
    #     )

    # def remove_stall_by_name(self, arguments: Union[str, dict]) -> str:
    #     """
    #     Remove from Nostr a stall and its products by name

    #     Args:
    #         arguments: str or dict with the stall name. Can be in formats:
    #             - {"name": "stall_name"}
    #             - {"arguments": "{\"name\": \"stall_name\"}"}
    #             - "stall_name"

    #     Returns:
    #         str: JSON array with status of the operation

    #     Raises:
    #         ValueError: if NostrClient is not initialized
    #     """
    #     if self._nostr_client is None:
    #         logger.error("NostrClient not initialized")
    #         raise ValueError("NostrClient not initialized")

    #     try:
    #         # Parse arguments to get stall_name
    #         stall_name: str
    #         if isinstance(arguments, str):
    #             try:
    #                 parsed = json.loads(arguments)
    #                 if isinstance(parsed, dict):
    #                     raw_name: Optional[Any] = parsed.get("name")
    #                     stall_name = str(raw_name) if raw_name is not None else ""
    #                 else:
    #                     stall_name = arguments
    #             except json.JSONDecodeError:
    #                 stall_name = arguments
    #         else:
    #             if "arguments" in arguments:
    #                 nested = json.loads(arguments["arguments"])
    #                 if isinstance(nested, dict):
    #                     raw_name = nested.get("name")
    #                     stall_name = str(raw_name) if raw_name is not None else ""
    #                 else:
    #                     raw_name = nested
    #                     stall_name = str(raw_name) if raw_name is not None else ""
    #             else:
    #                 raw_name = arguments.get("name", arguments)
    #                 stall_name = str(raw_name) if raw_name is not None else ""

    #         results = []
    #         stall_index = None
    #         stall_id = None

    #         # Find the stall and its event_id in the stall_db
    #         for i, (stall, event_id) in enumerate(self.stall_db):
    #             if stall.name == stall_name:
    #                 stall_index = i
    #                 stall_id = stall.id
    #                 break

    #         # If stall_id is empty, then we found no match
    #         if stall_id is None:
    #             return json.dumps(
    #                 [
    #                     {
    #                         "status": "error",
    #                         "message": f"Stall '{stall_name}' not found in database",
    #                         "stall_name": stall_name,
    #                     }
    #                 ]
    #             )

    #         # First remove all products in this stall
    #         for i, (product, event_id) in enumerate(self.product_db):
    #             if product.stall_id == stall_id:
    #                 if event_id is None:
    #                     results.append(
    #                         {
    #                             "status": "skipped",
    #                             "message": "Unpublished product",
    #                             "product_name": product.name,
    #                             "stall_name": stall_name,
    #                         }
    #                     )
    #                     continue

    #                 try:
    #                     self._nostr_client.delete_event(
    #                         event_id, reason=f"Stall for '{product.name}' removed"
    #                     )
    #                     self.product_db[i] = (product, None)
    #                     results.append(
    #                         {
    #                             "status": "success",
    #                             "message": f"Product '{product.name}' removed",
    #                             "product_name": product.name,
    #                             "stall_name": stall_name,
    #                             "event_id": str(event_id),
    #                         }
    #                     )
    #                     # Pause for 0.5 seconds to avoid rate limiting
    #                     time.sleep(0.5)
    #                 except RuntimeError as e:
    #                     logger.error(
    #                         "Unable to remove product %s. Error %s", product, e
    #                     )
    #                     results.append(
    #                         {
    #                             "status": "error",
    #                             "message": str(e),
    #                             "product_name": product.name,
    #                             "stall_name": stall_name,
    #                         }
    #                     )

    #         # Now remove the stall itself
    #         if stall_index is not None:
    #             _, stall_event_id = self.stall_db[stall_index]
    #             if stall_event_id is None:
    #                 results.append(
    #                     {
    #                         "status": "skipped",
    #                         "message": (
    #                             f"Stall '{stall_name}' has not been published yet"
    #                         ),
    #                         "stall_name": stall_name,
    #                     }
    #                 )
    #             else:
    #                 try:
    #                     self._nostr_client.delete_event(
    #                         stall_event_id, reason=f"Stall '{stall_name}' removed"
    #                     )
    #                     self.stall_db[stall_index] = (
    #                         self.stall_db[stall_index][0],
    #                         None,
    #                     )
    #                     results.append(
    #                         {
    #                             "status": "success",
    #                             "message": f"Stall '{stall_name}' removed",
    #                             "stall_name": stall_name,
    #                             "event_id": str(stall_event_id),
    #                         }
    #                     )
    #                 except RuntimeError as e:
    #                     logger.error(
    #                         "Unable to remove stall %s. Error %s", stall_name, e
    #                     )
    #                     results.append(
    #                         {
    #                             "status": "error",
    #                             "message": str(e),
    #                             "stall_name": stall_name,
    #                         }
    #                     )

    #         return json.dumps(results)

    #     except RuntimeError as e:
    #         logger.error("Unable to remove stall '%s'. Error %s", stall_name, e)
    #         return json.dumps(
    #             [{"status": "error", "message": str(e), "stall_name": "unknown"}]
    #         )

    def _create_payment_request(
        self,
        order_id: str,
        payment_type: str,
        payment_url: str,
    ) -> str:
        """
        Create a payment request in JSON format.

        Args:
            order_id (str): ID of the order.
            payment_type (PaymentType): Type of payment.
            payment_url (str): URL of the payment.

        Returns:
            str: JSON string of the payment request.
        """

        payment_request = {
            "id": order_id,
            "type": 1,
            "message": "Thank you for your business!",
            "payment_options": [{"type": payment_type.lower(), "link": payment_url}],
        }

        return json.dumps(
            payment_request, indent=2
        )  # Convert to JSON string with pretty printing
