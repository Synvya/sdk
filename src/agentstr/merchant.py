import json
import logging
from typing import Any, List, Optional, Tuple, Union

from agentstr.nostr import (
    AgentProfile,
    EventId,
    Keys,
    NostrClient,
    ProductData,
    ShippingCost,
    ShippingMethod,
    StallData,
)

try:
    from phi.tools import Toolkit
except ImportError:
    raise ImportError(
        "`phidata` not installed. Please install using `pip install phidata`"
    )

from pydantic import BaseModel, ConfigDict


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
            specs=product.specs if product.specs is not None else [],
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
            specs=self.specs,
        )

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the MerchantProduct.
        ShippingCost class is not serializable, so we need to convert it to a dictionary.

        Returns:
            dict: dictionary representation of the MerchantProduct
        """
        shipping_dicts = []
        for shipping in self.shipping:
            shipping_dicts.append({"id": shipping.id, "cost": shipping.cost})

        return {
            "id": self.id,
            "stall_id": self.stall_id,
            "name": self.name,
            "description": self.description,
            "images": self.images,
            "currency": self.currency,
            "price": self.price,
            "quantity": self.quantity,
            "shipping": shipping_dicts,
            "categories": self.categories,
            "specs": self.specs,
        }


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
            shipping=stall.shipping(),
        )

    def to_stall_data(self) -> StallData:
        return StallData(
            self.id,
            self.name,
            self.description,
            self.currency,
            self.shipping,  # No conversion needed
        )

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the MerchantStall.
        ShippingMethod class is not serializable, so we need to convert it to a dictionary.
        We can only access cost and id from the ShippingMethod class. We can't access name or regions.

        Returns:
            dict: dictionary representation of the MerchantStall
        """
        shipping_dicts = []
        for shipping in self.shipping:
            shipping_dicts.append(
                {
                    "cost": shipping.get_shipping_cost().cost,
                    "id": shipping.get_shipping_cost().id,
                }
            )

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "currency": self.currency,
            "shipping zones": [shipping_dicts],
        }


class Merchant(Toolkit):
    """
    Merchant is a toolkit that allows a merchant to publish products and stalls to Nostr.

    TBD:
    - Better differentiation between products and stalls in the database and products and stalls published.

    """

    from pydantic import ConfigDict

    model_config = ConfigDict(
        arbitrary_types_allowed=True, extra="allow", validate_assignment=True
    )

    _nostr_client: Optional[NostrClient] = None
    product_db: List[Tuple[MerchantProduct, Optional[EventId]]] = []
    stall_db: List[Tuple[MerchantStall, Optional[EventId]]] = []

    def __init__(
        self,
        merchant_profile: AgentProfile,
        relay: str,
        stalls: List[MerchantStall],
        products: List[MerchantProduct],
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
        self._nostr_client = NostrClient(relay, merchant_profile.get_private_key())

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
        Retrieves merchant profile in JSON format

        Returns:
            str: merchant profile in JSON format
        """
        return json.dumps(self.merchant_profile.to_json())

    def get_relay(self) -> str:
        """
        Retrieves the Nostr relay the merchant is using

        Returns:
            str: Nostr relay
        """
        return self.relay

    def get_products(self) -> str:
        """
        Retrieves all the merchant products

        Returns:
            str: JSON string containing all products
        """
        return json.dumps([p.to_dict() for p, _ in self.product_db])

    def get_stalls(self) -> str:
        """
        Retrieves all the merchant stalls in JSON format

        Returns:
            str: JSON string containing all stalls
        """
        return json.dumps([s.to_dict() for s, _ in self.stall_db])

    def publish_all_products(
        self,
    ) -> str:
        """
        Publishes or updates all products in the Merchant's Product DB

        Returns:
            str: JSON array with status of all product publishing operations
        """

        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        results = []

        for i, (product, _) in enumerate(self.product_db):
            try:
                # Convert MerchantProduct to ProductData for nostr_client
                product_data = product.to_product_data()
                # Publish using the SDK's synchronous method
                event_id = self._nostr_client.publish_product(product_data)
                self.product_db[i] = (product, event_id)
                results.append(
                    {
                        "status": "success",
                        "event_id": str(event_id),
                        "product_name": product.name,
                    }
                )
            except Exception as e:
                logging.error(f"Unable to publish product {product}. Error {e}")
                results.append(
                    {"status": "error", "message": str(e), "product_name": product.name}
                )

        return json.dumps(results)

    def publish_all_stalls(
        self,
    ) -> str:
        """
        Publishes or updates all stalls managed by the merchant and adds the corresponding EventId to the Stall DB

        Returns:
            str: JSON array with status of all stall publishing operations
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")
        results = []

        for i, (stall, _) in enumerate(self.stall_db):
            try:
                # Convert MerchantStall to StallData for nostr_client
                stall_data = stall.to_stall_data()
                event_id = self._nostr_client.publish_stall(stall_data)
                self.stall_db[i] = (stall, event_id)
                results.append(
                    {
                        "status": "success",
                        "event_id": str(event_id),
                        "stall_name": stall.name,
                    }
                )
            except Exception as e:
                logging.error(f"Unable to publish stall {stall}. Error {e}")
                results.append(
                    {"status": "error", "message": str(e), "stall_name": stall.name}
                )

        return json.dumps(results)

    def publish_new_product(self, product: MerchantProduct) -> str:
        """
        Publishes a new product that is not currently in the Merchant's Product DB and adds it to the Product DB

        Args:
            product: MerchantProduct to be published

        Returns:
            str: JSON string with status of the operation
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
        except Exception as e:
            return json.dumps(
                {"status": "error", "message": str(e), "product_name": product.name}
            )

    def publish_product_by_name(self, arguments: str) -> str:
        """
        Publishes or updates a given product from the Merchant's Product DB
        Args:
            arguments: JSON string that may contain {"name": "product_name"} or just "product_name"

        Returns:
            str: JSON string with status of the operation
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
                    product_data = product.to_product_data()
                    # Publish using the SDK's synchronous method
                    event_id = self._nostr_client.publish_product(product_data)
                    # Update the product_db with the new event_id
                    self.product_db[i] = (product, event_id)
                    return json.dumps(
                        {
                            "status": "success",
                            "event_id": str(event_id),
                            "product_name": product.name,
                        }
                    )
                except Exception as e:
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
        Publishes or updates all products sold by the merchant in a given stall

        Args:
            arguments: str or dict with the stall name. Can be in formats:
                - {"name": "stall_name"}
                - {"arguments": "{\"name\": \"stall_name\"}"}
                - "stall_name"

        Returns:
            str: JSON array with status of all product publishing operations
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
                        product_data = product.to_product_data()
                        event_id = self._nostr_client.publish_product(product_data)
                        self.product_db[i] = (product, event_id)
                        results.append(
                            {
                                "status": "success",
                                "event_id": str(event_id),
                                "product_name": product.name,
                                "stall_name": stall_name,
                            }
                        )
                    except Exception as e:
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

        except Exception as e:
            return json.dumps(
                [{"status": "error", "message": str(e), "arguments": str(arguments)}]
            )

    def publish_profile(self) -> str:
        """
        Publishes the profile on Nostr

        Returns:
            str: JSON of the event that published the profile

        Raises:
            RuntimeError: if it can't publish the event
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        try:
            event_id = self._nostr_client.publish_profile(
                self.merchant_profile.get_name(),
                self.merchant_profile.get_about(),
                self.merchant_profile.get_picture(),
            )
            return json.dumps(event_id.__dict__)
        except Exception as e:
            raise RuntimeError(f"Unable to publish the profile: {e}")

    def publish_new_stall(self, stall: MerchantStall) -> str:
        """
        Publishes a new stall that is not currently in the Merchant's Stall DB and adds it to the Stall DB

        Args:
            stall: MerchantStall to be published

        Returns:
            str: JSON string with status of the operation
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        try:
            # Convert to StallData for SDK
            stall_data = stall.to_stall_data()
            # Publish using the SDK's synchronous method
            event_id = self._nostr_client.publish_stall(stall_data)
            # we need to add the stall event id to the stall db
            self.stall_db.append((stall, event_id))
            return json.dumps(
                {
                    "status": "success",
                    "event_id": str(event_id),
                    "stall_name": stall.name,
                }
            )
        except Exception as e:
            return json.dumps(
                {"status": "error", "message": str(e), "stall_name": stall.name}
            )

    def publish_stall_by_name(self, arguments: Union[str, dict]) -> str:
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
                        stall_data = stall.to_stall_data()
                        event_id = self._nostr_client.publish_stall(stall_data)
                        self.stall_db[i] = (stall, event_id)
                        return json.dumps(
                            {
                                "status": "success",
                                "event_id": str(event_id),
                                "stall_name": stall.name,
                            }
                        )
                    except Exception as e:
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

        except Exception as e:
            return json.dumps(
                [{"status": "error", "message": str(e), "stall_name": "unknown"}]
            )

    def remove_all_products(self) -> str:
        """
        Removes all published products from Nostr

        Returns:
            str: JSON array with status of all product removal operations
        """
        if self._nostr_client is None:
            raise ValueError("NostrClient not initialized")

        results = []

        for i, (product, event_id) in enumerate(self.product_db):
            if event_id is None:
                results.append(
                    {
                        "status": "skipped",
                        "message": f"Product '{product.name}' has not been published yet",
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
            except Exception as e:
                results.append(
                    {"status": "error", "message": str(e), "product_name": product.name}
                )

        return json.dumps(results)

    def remove_all_stalls(self) -> str:
        """
        Removes all stalls and their products from Nostr

        Returns:
            str: JSON array with status of all removal operations
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
                                "message": f"Product '{product.name}' has not been published yet",
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
                    except Exception as e:
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
                        "message": f"Stall '{stall_name}' has not been published yet",
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
                except Exception as e:
                    results.append(
                        {"status": "error", "message": str(e), "stall_name": stall_name}
                    )

        return json.dumps(results)

    def remove_product_by_name(self, arguments: str) -> str:
        """
        Deletes a product with the given name from Nostr

        Args:
            arguments: JSON string that may contain {"name": "product_name"} or just "product_name"

        Returns:
            str: JSON string with status of the operation
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
                    return json.dumps(
                        {
                            "status": "success",
                            "message": f"Product '{name}' removed",
                            "product_name": name,
                            "event_id": str(event_id),
                        }
                    )
                except Exception as e:
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
        """Remove a stall and its products by name

        Args:
            arguments: str or dict with the stall name. Can be in formats:
                - {"name": "stall_name"}
                - {"arguments": "{\"name\": \"stall_name\"}"}
                - "stall_name"

        Returns:
            str: JSON array with status of the operation
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
                                "message": f"Product '{product.name}' has not been published yet",
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
                    except Exception as e:
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
                            "message": f"Stall '{stall_name}' has not been published yet",
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
                    except Exception as e:
                        results.append(
                            {
                                "status": "error",
                                "message": str(e),
                                "stall_name": stall_name,
                            }
                        )

            return json.dumps(results)

        except Exception as e:
            return json.dumps(
                [{"status": "error", "message": str(e), "stall_name": "unknown"}]
            )

    def get_event_id(self, response: Any) -> str:
        """Convert any response to a string event ID.

        Args:
            response: Response that might contain an event ID

        Returns:
            str: String representation of event ID or empty string if None
        """
        if response is None:
            return ""
        return str(response)
