"""
Module implementing the MerchantTools Toolkit for Agno agents.
"""

import json
import logging
import time
from typing import Any, List, Optional, Tuple, Union

from nostr_sdk import EventId
from pydantic import ConfigDict

from synvya_sdk import NostrClient, Product, Stall

try:
    from agno.tools import Toolkit
except ImportError as exc:
    raise ImportError(
        "`agno` not installed. Please install using `pip install agno`"
    ) from exc


class SellerTools(Toolkit):
    """
    SellerTools is a toolkit that allows a seller to publish
    products and stalls to Nostr.

    TBD:
    - Better differentiation between products and stalls in the database
    and products and stalls published.

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
        self.profile = self._nostr_client.get_profile()

        # initialize the Product DB with no event id
        self.product_db = [(product, None) for product in products]

        # initialize the Stall DB with no event id
        self.stall_db = [(stall, None) for stall in stalls]

        # Register methods
        self.register(self.get_profile)
        self.register(self.get_relay)
        self.register(self.get_products)
        self.register(self.get_stalls)
        self.register(self.publish_all_products)
        self.register(self.publish_all_stalls)
        self.register(self.publish_new_product)
        self.register(self.publish_product_by_name)
        self.register(self.publish_products_by_stall_name)
        self.register(self.publish_profile)
        self.register(self.publish_new_stall)
        self.register(self.publish_stall_by_name)
        self.register(self.remove_all_products)
        self.register(self.remove_all_stalls)
        self.register(self.remove_product_by_name)
        self.register(self.remove_stall_by_name)

    def get_profile(self) -> str:
        """
        Get the merchant profile in JSON format

        Returns:
            str: merchant profile in JSON format
        """
        return json.dumps(self.profile.to_json())

    def get_relay(self) -> str:
        """
        Get the Nostr relay the merchant is using

        Returns:
            str: Nostr relay
        """
        return self.relay

    def get_products(self) -> str:
        """
        Get all the merchant products

        Returns:
            str: JSON string containing all products
        """
        return json.dumps([p.to_dict() for p, _ in self.product_db])

    def get_stalls(self) -> str:
        """
        Get all the merchant stalls in JSON format

        Returns:
            str: JSON string containing all stalls
        """
        return json.dumps([s.to_dict() for s, _ in self.stall_db])

    def publish_all_products(
        self,
    ) -> str:
        """
        Publishes or updates to Nostrall products in the Merchant's Product DB

        Returns:
            str: JSON array with status of all product publishing operations

        Raises:
            ValueError: if NostrClient is not initialized
        """

        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        results = []

        for i, (product, _) in enumerate(self.product_db):
            try:
                # Convert MerchantProduct to ProductData for nostr_client
                # product_data = product.to_product_data()
                # Publish using the SDK's synchronous method
                event_id = self._nostr_client.publish_product(product)
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
                logging.error("Unable to publish product %s. Error %s", product, e)
                results.append(
                    {"status": "error", "message": str(e), "product_name": product.name}
                )

        return json.dumps(results)

    def publish_all_stalls(
        self,
    ) -> str:
        """
        Publishes or updates to Nostr all stalls managed by the merchant and adds
        the corresponding EventId to the Stall DB

        Returns:
            str: JSON array with status of all stall publishing operations

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")
        results = []

        for i, (stall, _) in enumerate(self.stall_db):
            try:
                # We don't need to convert MerchantStall to StallData for nostr_client
                # stall_data = stall.to_stall_data()
                event_id = self._nostr_client.publish_stall(stall)
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
                logging.error("Unable to publish stall %s. Error %s", stall, e)
                results.append(
                    {"status": "error", "message": str(e), "stall_name": stall.name}
                )

        return json.dumps(results)

    def publish_new_product(self, product: Product) -> str:
        """
        Publishes to Nostra new product that is not currently in the Merchant's
        Product DB and adds it to the Product DB

        Args:
            product: Product to be published

        Returns:
            str: JSON string with status of the operation

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        try:
            # Convert MerchantProduct to ProductData for nostr_client
            product_data = product.to_product_data()
            # Publish using the SDK's synchronous method
            event_id = self._nostr_client.publish_product(product_data)
            # we need to add the product event id to the product db
            self.product_db.append((product, event_id))
            return json.dumps(
                {
                    "status": "success",
                    "event_id": str(event_id),
                    "product_name": product.name,
                }
            )
        except RuntimeError as e:
            return json.dumps(
                {"status": "error", "message": str(e), "product_name": product.name}
            )

    def publish_product_by_name(self, arguments: str) -> str:
        """
        Publishes or updates to Nostra given product from the Merchant's Product DB
        Args:
            arguments: JSON string that may contain
            {"name": "product_name"} or just "product_name"

        Returns:
            str: JSON string with status of the operation

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        try:
            # Try to parse as JSON first
            if isinstance(arguments, dict):
                parsed = arguments
            else:
                parsed = json.loads(arguments)
            name = parsed.get(
                "name", parsed
            )  # Get name if exists, otherwise use whole value
        except json.JSONDecodeError:
            # If not JSON, use the raw string
            name = arguments

        # iterate through all products searching for the right name
        for i, (product, _) in enumerate(self.product_db):
            if product.name == name:
                try:
                    # Convert MerchantProduct to ProductData for nostr_client
                    # product_data = product.to_product_data()
                    # Publish using the SDK's synchronous method
                    event_id = self._nostr_client.publish_product(product)
                    # Update the product_db with the new event_id
                    self.product_db[i] = (product, event_id)
                    # Pause for 0.5 seconds to avoid rate limiting
                    time.sleep(0.5)
                    return json.dumps(
                        {
                            "status": "success",
                            "event_id": str(event_id),
                            "product_name": product.name,
                        }
                    )
                except RuntimeError as e:
                    return json.dumps(
                        {
                            "status": "error",
                            "message": str(e),
                            "product_name": product.name,
                        }
                    )

        # If we are here, then we didn't find a match
        return json.dumps(
            {
                "status": "error",
                "message": f"Product '{name}' not found in database",
                "product_name": name,
            }
        )

    def publish_products_by_stall_name(self, arguments: Union[str, dict]) -> str:
        """
        Publishes or updates to Nostr all products sold by the merchant in a given stall

        Args:
            arguments: str or dict with the stall name. Can be in formats:
                - {"name": "stall_name"}
                - {"arguments": "{\"name\": \"stall_name\"}"}
                - "stall_name"

        Returns:
            str: JSON array with status of all product publishing operations

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        try:
            # Parse arguments to get stall_name
            stall_name: str
            if isinstance(arguments, str):
                try:
                    parsed = json.loads(arguments)
                    if isinstance(parsed, dict):
                        raw_name: Optional[Any] = parsed.get("name")
                        stall_name = str(raw_name) if raw_name is not None else ""
                    else:
                        stall_name = arguments
                except json.JSONDecodeError:
                    stall_name = arguments
            else:
                if "arguments" in arguments:
                    nested = json.loads(arguments["arguments"])
                    if isinstance(nested, dict):
                        raw_name = nested.get("name")
                        stall_name = str(raw_name) if raw_name is not None else ""
                    else:
                        raw_name = nested
                        stall_name = str(raw_name) if raw_name is not None else ""
                else:
                    raw_name = arguments.get("name", arguments)
                    stall_name = str(raw_name) if raw_name is not None else ""

            results = []
            stall_id = None

            # Find stall ID
            for stall, _ in self.stall_db:
                if stall.name == stall_name:
                    stall_id = stall.id
                    break

            if stall_id is None:
                return json.dumps(
                    [
                        {
                            "status": "error",
                            "message": f"Stall '{stall_name}' not found in database",
                            "stall_name": stall_name,
                        }
                    ]
                )

            # Publish products
            for i, (product, _) in enumerate(self.product_db):
                if product.stall_id == stall_id:
                    try:
                        # product_data = product.to_product_data()
                        event_id = self._nostr_client.publish_product(product)
                        self.product_db[i] = (product, event_id)
                        results.append(
                            {
                                "status": "success",
                                "event_id": str(event_id),
                                "product_name": product.name,
                                "stall_name": stall_name,
                            }
                        )
                        # Pause for 0.5 seconds to avoid rate limiting
                        time.sleep(0.5)
                    except RuntimeError as e:
                        results.append(
                            {
                                "status": "error",
                                "message": str(e),
                                "product_name": product.name,
                                "stall_name": stall_name,
                            }
                        )

            if not results:
                return json.dumps(
                    [
                        {
                            "status": "error",
                            "message": f"No products found in stall '{stall_name}'",
                            "stall_name": stall_name,
                        }
                    ]
                )

            return json.dumps(results)

        except RuntimeError as e:
            return json.dumps(
                [{"status": "error", "message": str(e), "arguments": str(arguments)}]
            )

    def publish_profile(self) -> str:
        """
        Publishes the profile to Nostr

        Returns:
            str: id of the event publishing the profile

        Raises:
            RuntimeError: if it can't publish the event
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        try:
            return self._nostr_client.publish_profile()
        except RuntimeError as e:
            raise RuntimeError(f"Unable to publish the profile: {e}") from e

    def publish_new_stall(self, stall: Stall) -> str:
        """
        Publishes to Nostr a new stall that is not currently in the Merchant's
        Stall DB and adds it to the Stall DB

        Args:
            stall: Stall to be published

        Returns:
            str: JSON string with status of the operation

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        try:
            # We don't ned to convert to StallData.
            # nostr_client.publish_stall() accepts a MerchantStall
            # stall_data = stall.to_stall_data()
            # Publish using the  synchronous method
            event_id = self._nostr_client.publish_stall(stall)
            # we need to add the stall event id to the stall db
            self.stall_db.append((stall, event_id))
            return json.dumps(
                {
                    "status": "success",
                    "event_id": str(event_id),
                    "stall_name": stall.name,
                }
            )
        except RuntimeError as e:
            return json.dumps(
                {"status": "error", "message": str(e), "stall_name": stall.name}
            )

    def publish_stall_by_name(self, arguments: Union[str, dict]) -> str:
        """
        Publishes or updates to Nostr a given stall by name

        Args:
            arguments: str or dict with the stall name. Can be in formats:
                - {"name": "stall_name"}
                - {"arguments": "{\"name\": \"stall_name\"}"}
                - "stall_name"

        Returns:
            str: JSON array with status of the operation

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        try:
            # Parse arguments to get stall_name
            stall_name: str
            if isinstance(arguments, str):
                try:
                    # Try to parse as JSON first
                    parsed = json.loads(arguments)
                    if isinstance(parsed, dict):
                        raw_name: Optional[Any] = parsed.get("name")
                        stall_name = str(raw_name) if raw_name is not None else ""
                    else:
                        stall_name = arguments
                except json.JSONDecodeError:
                    # If not JSON, use the raw string
                    stall_name = arguments
            else:
                # Handle dict input
                if "arguments" in arguments:
                    nested = json.loads(arguments["arguments"])
                    if isinstance(nested, dict):
                        raw_name = nested.get("name")
                        stall_name = str(raw_name) if raw_name is not None else ""
                    else:
                        raw_name = nested
                        stall_name = str(raw_name) if raw_name is not None else ""
                else:
                    raw_name = arguments.get("name", arguments)
                    stall_name = str(raw_name) if raw_name is not None else ""

            # Find and publish stall
            for i, (stall, _) in enumerate(self.stall_db):
                if stall.name == stall_name:
                    try:
                        event_id = self._nostr_client.publish_stall(stall)
                        self.stall_db[i] = (stall, event_id)
                        # Pause for 0.5 seconds to avoid rate limiting
                        time.sleep(0.5)
                        return json.dumps(
                            {
                                "status": "success",
                                "event_id": str(event_id),
                                "stall_name": stall.name,
                            }
                        )

                    except RuntimeError as e:
                        return json.dumps(
                            [
                                {
                                    "status": "error",
                                    "message": str(e),
                                    "stall_name": stall.name,
                                }
                            ]
                        )

            # Stall not found
            return json.dumps(
                [
                    {
                        "status": "error",
                        "message": f"Stall '{stall_name}' not found in database",
                        "stall_name": stall_name,
                    }
                ]
            )

        except RuntimeError as e:
            return json.dumps(
                [{"status": "error", "message": str(e), "stall_name": "unknown"}]
            )

    def remove_all_products(self) -> str:
        """
        Removes from Nostr all products published by the merchant

        Returns:
            str: JSON array with status of all product removal operations

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        results = []

        for i, (product, event_id) in enumerate(self.product_db):
            if event_id is None:
                results.append(
                    {
                        "status": "skipped",
                        "message": (
                            f"Product '{product.name}' has not been published yet"
                        ),
                        "product_name": product.name,
                    }
                )
                continue

            try:
                # Delete the event using the SDK's method
                self._nostr_client.delete_event(
                    event_id, reason=f"Product '{product.name}' removed"
                )
                # Remove the event_id, keeping the product in the database
                self.product_db[i] = (product, None)
                results.append(
                    {
                        "status": "success",
                        "message": f"Product '{product.name}' removed",
                        "product_name": product.name,
                        "event_id": str(event_id),
                    }
                )
                # Pause for 0.5 seconds to avoid rate limiting
                time.sleep(0.5)
            except RuntimeError as e:
                results.append(
                    {"status": "error", "message": str(e), "product_name": product.name}
                )

        return json.dumps(results)

    def remove_all_stalls(self) -> str:
        """
        Removes from Nostr all stalls from the merchant and their
        corresponding products

        Returns:
            str: JSON array with status of all removal operations

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        results = []

        # First remove all products from all stalls
        for i, (stall, _) in enumerate(self.stall_db):
            stall_name = stall.name
            stall_id = stall.id

            # Remove all products in this stall
            for j, (product, event_id) in enumerate(self.product_db):
                if product.stall_id == stall_id:
                    if event_id is None:
                        results.append(
                            {
                                "status": "skipped",
                                "message": "Unpublished product",
                                "product_name": product.name,
                                "stall_name": stall_name,
                            }
                        )
                        continue

                    try:
                        self._nostr_client.delete_event(
                            event_id,
                            reason=f"Stall for product '{product.name}' removed",
                        )
                        self.product_db[j] = (product, None)
                        results.append(
                            {
                                "status": "success",
                                "message": f"Product '{product.name}' removed",
                                "product_name": product.name,
                                "stall_name": stall_name,
                                "event_id": str(event_id),
                            }
                        )
                    except RuntimeError as e:
                        results.append(
                            {
                                "status": "error",
                                "message": str(e),
                                "product_name": product.name,
                                "stall_name": stall_name,
                            }
                        )

            # Now remove the stall itself
            _, stall_event_id = self.stall_db[i]
            if stall_event_id is None:
                results.append(
                    {
                        "status": "skipped",
                        "message": (f"Stall '{stall_name}' has not been published yet"),
                        "stall_name": stall_name,
                    }
                )
            else:
                try:
                    self._nostr_client.delete_event(
                        stall_event_id, reason=f"Stall '{stall_name}' removed"
                    )
                    self.stall_db[i] = (stall, None)
                    results.append(
                        {
                            "status": "success",
                            "message": f"Stall '{stall_name}' removed",
                            "stall_name": stall_name,
                            "event_id": str(stall_event_id),
                        }
                    )
                    # Pause for 0.5 seconds to avoid rate limiting
                    time.sleep(0.5)
                except RuntimeError as e:
                    results.append(
                        {"status": "error", "message": str(e), "stall_name": stall_name}
                    )

        return json.dumps(results)

    def remove_product_by_name(self, arguments: str) -> str:
        """
        Removes from Nostr a product with the given name

        Args:
            arguments: JSON string that may contain {"name": "product_name"}
            or just "product_name"

        Returns:
            str: JSON string with status of the operation

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        try:
            # Try to parse as JSON first
            if isinstance(arguments, dict):
                parsed = arguments
            else:
                parsed = json.loads(arguments)
            name = parsed.get(
                "name", parsed
            )  # Get name if exists, otherwise use whole value
        except json.JSONDecodeError:
            # If not JSON, use the raw string
            name = arguments

        # Find the product and its event_id in the product_db
        for i, (product, event_id) in enumerate(self.product_db):
            if product.name == name:
                if event_id is None:
                    return json.dumps(
                        {
                            "status": "error",
                            "message": f"Product '{name}' has not been published yet",
                            "product_name": name,
                        }
                    )

                try:
                    # Delete the event using the SDK's method
                    self._nostr_client.delete_event(
                        event_id, reason=f"Product '{name}' removed"
                    )
                    # Remove the event_id, keeping the product in the database
                    self.product_db[i] = (product, None)
                    # Pause for 0.5 seconds to avoid rate limiting
                    time.sleep(0.5)
                    return json.dumps(
                        {
                            "status": "success",
                            "message": f"Product '{name}' removed",
                            "product_name": name,
                            "event_id": str(event_id),
                        }
                    )
                except RuntimeError as e:
                    return json.dumps(
                        {"status": "error", "message": str(e), "product_name": name}
                    )

        # If we get here, we didn't find the product
        return json.dumps(
            {
                "status": "error",
                "message": f"Product '{name}' not found in database",
                "product_name": name,
            }
        )

    def remove_stall_by_name(self, arguments: Union[str, dict]) -> str:
        """
        Remove from Nostr a stall and its products by name

        Args:
            arguments: str or dict with the stall name. Can be in formats:
                - {"name": "stall_name"}
                - {"arguments": "{\"name\": \"stall_name\"}"}
                - "stall_name"

        Returns:
            str: JSON array with status of the operation

        Raises:
            ValueError: if NostrClient is not initialized
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        try:
            # Parse arguments to get stall_name
            stall_name: str
            if isinstance(arguments, str):
                try:
                    parsed = json.loads(arguments)
                    if isinstance(parsed, dict):
                        raw_name: Optional[Any] = parsed.get("name")
                        stall_name = str(raw_name) if raw_name is not None else ""
                    else:
                        stall_name = arguments
                except json.JSONDecodeError:
                    stall_name = arguments
            else:
                if "arguments" in arguments:
                    nested = json.loads(arguments["arguments"])
                    if isinstance(nested, dict):
                        raw_name = nested.get("name")
                        stall_name = str(raw_name) if raw_name is not None else ""
                    else:
                        raw_name = nested
                        stall_name = str(raw_name) if raw_name is not None else ""
                else:
                    raw_name = arguments.get("name", arguments)
                    stall_name = str(raw_name) if raw_name is not None else ""

            results = []
            stall_index = None
            stall_id = None

            # Find the stall and its event_id in the stall_db
            for i, (stall, event_id) in enumerate(self.stall_db):
                if stall.name == stall_name:
                    stall_index = i
                    stall_id = stall.id
                    break

            # If stall_id is empty, then we found no match
            if stall_id is None:
                return json.dumps(
                    [
                        {
                            "status": "error",
                            "message": f"Stall '{stall_name}' not found in database",
                            "stall_name": stall_name,
                        }
                    ]
                )

            # First remove all products in this stall
            for i, (product, event_id) in enumerate(self.product_db):
                if product.stall_id == stall_id:
                    if event_id is None:
                        results.append(
                            {
                                "status": "skipped",
                                "message": "Unpublished product",
                                "product_name": product.name,
                                "stall_name": stall_name,
                            }
                        )
                        continue

                    try:
                        self._nostr_client.delete_event(
                            event_id, reason=f"Stall for '{product.name}' removed"
                        )
                        self.product_db[i] = (product, None)
                        results.append(
                            {
                                "status": "success",
                                "message": f"Product '{product.name}' removed",
                                "product_name": product.name,
                                "stall_name": stall_name,
                                "event_id": str(event_id),
                            }
                        )
                        # Pause for 0.5 seconds to avoid rate limiting
                        time.sleep(0.5)
                    except RuntimeError as e:
                        results.append(
                            {
                                "status": "error",
                                "message": str(e),
                                "product_name": product.name,
                                "stall_name": stall_name,
                            }
                        )

            # Now remove the stall itself
            if stall_index is not None:
                _, stall_event_id = self.stall_db[stall_index]
                if stall_event_id is None:
                    results.append(
                        {
                            "status": "skipped",
                            "message": (
                                f"Stall '{stall_name}' has not been published yet"
                            ),
                            "stall_name": stall_name,
                        }
                    )
                else:
                    try:
                        self._nostr_client.delete_event(
                            stall_event_id, reason=f"Stall '{stall_name}' removed"
                        )
                        self.stall_db[stall_index] = (
                            self.stall_db[stall_index][0],
                            None,
                        )
                        results.append(
                            {
                                "status": "success",
                                "message": f"Stall '{stall_name}' removed",
                                "stall_name": stall_name,
                                "event_id": str(stall_event_id),
                            }
                        )
                    except RuntimeError as e:
                        results.append(
                            {
                                "status": "error",
                                "message": str(e),
                                "stall_name": stall_name,
                            }
                        )

            return json.dumps(results)

        except RuntimeError as e:
            return json.dumps(
                [{"status": "error", "message": str(e), "stall_name": "unknown"}]
            )
