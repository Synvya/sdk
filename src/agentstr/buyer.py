import json
import logging
from uuid import uuid4

from agno.agent import AgentKnowledge  # type: ignore
from agno.document.base import Document

from agentstr.models import AgentProfile, NostrProfile
from agentstr.nostr import NostrClient, PublicKey

try:
    from agno.tools import Toolkit
except ImportError:
    raise ImportError("`agno` not installed. Please install using `pip install agno`")


def _map_location_to_geohash(location: str) -> str:
    """
    Map a location to a geohash.

    TBD: Implement this function. Returning a fixed geohash for now.

    Args:
        location: location to map to a geohash. Can be a zip code, city, state, country, or latitude and longitude.

    Returns:
        str: geohash of the location or empty string if location is not found
    """
    if "snoqualmie" in location.lower():
        return "C23Q7U36W"
    else:
        return ""


class BuyerTools(Toolkit):
    """
    BuyerTools is a toolkit that allows an agent to find sellers and transact with them over Nostr.

    Sellers are downloaded from the Nostr relay and cached.
    Sellers can be found by name or public key.
    Sellers cache can be refreshed from the Nostr relay.
    Sellers can be retrieved as a list of Nostr profiles.

    TBD: populate the sellers locations with info from stalls.
    """

    from pydantic import ConfigDict

    model_config = ConfigDict(
        arbitrary_types_allowed=True, extra="allow", validate_assignment=True
    )

    logger = logging.getLogger("Buyer")
    sellers: set[NostrProfile] = set()

    def __init__(
        self,
        knowledge_base: AgentKnowledge,
        buyer_profile: AgentProfile,
        relay: str,
    ) -> None:
        """Initialize the Buyer toolkit.

        Args:
            knowledge_base: knowledge base of the buyer agent
            buyer_profile: profile of the buyer using this agent
            relay: Nostr relay to use for communications
        """
        super().__init__(name="Buyer")

        self.relay = relay
        self.buyer_profile = buyer_profile
        self.knowledge_base = knowledge_base
        # Initialize fields
        self._nostr_client = NostrClient(relay, buyer_profile.get_private_key())

        # Register methods
        self.register(self.find_seller_by_name)
        self.register(self.find_seller_by_public_key)
        self.register(self.find_sellers_by_location)
        self.register(self.get_profile)
        self.register(self.get_relay)
        self.register(self.get_seller_stalls)
        self.register(self.get_seller_products)
        self.register(self.get_seller_count)
        self.register(self.get_sellers)
        self.register(self.refresh_sellers)
        self.register(self.purchase_product)

    def purchase_product(self, product: str) -> str:
        """Purchase a product.

        Args:
            product: JSON string with product to purchase
        """
        return json.dumps({"status": "success", "message": "Product purchased"})

    def find_seller_by_name(self, name: str) -> str:
        """Find a seller by name.

        Args:
            name: name of the seller to find

        Returns:
            str: JSON string with seller profile or error message
        """
        for seller in self.sellers:
            if seller.get_name() == name:
                response = seller.to_json()
                # self._store_response_in_knowledge_base(response)
                return response
        response = json.dumps({"status": "error", "message": "Seller not found"})
        self._store_response_in_knowledge_base(response)
        return response

    def find_seller_by_public_key(self, public_key: str) -> str:
        """Find a seller by public key.

        Args:
            public_key: bech32 encoded public key of the seller to find

        Returns:
            str: seller profile json string or error message
        """
        for seller in self.sellers:
            if seller.get_public_key() == public_key:
                response = seller.to_json()
                # self._store_response_in_knowledge_base(response)
                return response
        response = json.dumps({"status": "error", "message": "Seller not found"})
        self._store_response_in_knowledge_base(response)
        return response

    def find_sellers_by_location(self, location: str) -> str:
        """Find sellers by location.

        Args:
            location: location of the seller to find (e.g. "San Francisco, CA")

        Returns:
            str: list of seller profile json strings or error message
        """
        sellers: set[NostrProfile] = set()
        geohash = _map_location_to_geohash(location)
        # print(f"find_sellers_by_location: geohash: {geohash}")

        if not geohash:
            response = json.dumps({"status": "error", "message": "Invalid location"})
            return response

        # Find sellers in the same geohash
        for seller in self.sellers:
            if geohash in seller.get_locations():
                # print(
                #     f"geohash {geohash} found in seller {seller.get_name()} with locations {seller.get_locations()}"
                # )
                sellers.add(seller)

        if not sellers:
            response = json.dumps(
                {"status": "error", "message": f"No sellers found near {location}"}
            )
            return response

        response = json.dumps([seller.to_dict() for seller in sellers])
        # print("find_sellers_by_location: storing response in knowledge base")
        self._store_response_in_knowledge_base(response)
        # print(f"Found {len(sellers)} sellers near {location}")
        return response

    def get_profile(self) -> str:
        """Get the Nostr profile of the buyer agent.

        Returns:
            str: buyer profile json string
        """
        response = self.buyer_profile.to_json()
        self._store_response_in_knowledge_base(response)
        return response

    def get_relay(self) -> str:
        """Get the Nostr relay that the buyer agent is using.

        Returns:
            str: Nostr relay
        """
        response = self.relay
        # self._store_response_in_knowledge_base(response)
        return response

    def get_seller_stalls(self, public_key: str) -> str:
        """Get the stalls from a seller.

        Args:
            public_key: public key of the seller

        Returns:
            str: JSON string with seller collections
        """
        try:
            stalls = self._nostr_client.retrieve_stalls_from_seller(
                PublicKey.parse(public_key)
            )
            response = json.dumps([stall.as_json() for stall in stalls])
            self._store_response_in_knowledge_base(response)
            return response
        except Exception as e:
            response = json.dumps({"status": "error", "message": str(e)})
            return response

    def get_seller_count(self) -> str:
        """Get the number of sellers.

        Returns:
            str: JSON string with status and count of sellers
        """
        response = json.dumps({"status": "success", "count": len(self.sellers)})
        return response

    def get_seller_products(self, public_key: str) -> str:
        """Get the products from a seller

        Args:
            public_key: public key of the seller

        Returns:
            str: JSON string with seller products
        """
        try:
            products = self._nostr_client.retrieve_products_from_seller(
                PublicKey.parse(public_key)
            )

            response = json.dumps([product.to_dict() for product in products])
            self._store_response_in_knowledge_base(response)
            return response
        except Exception as e:
            response = json.dumps({"status": "error", "message": str(e)})
            return response

    def get_sellers(self) -> str:
        """Get the list of sellers.
        If no sellers are cached, the list is refreshed from the Nostr relay.
        If sellers are cached, the list is returned from the cache.
        To get a fresh list of sellers, call refresh_sellers() sellers first.

        Returns:
            str: list of sellers json strings
        """
        if not self.sellers:
            self._refresh_sellers()
        response = json.dumps([seller.to_json() for seller in self.sellers])
        return response

    def refresh_sellers(self) -> str:
        """Refresh the list of sellers.

        Returns:
            str: JSON string with status and count of sellers refreshed
        """
        self._refresh_sellers()
        response = json.dumps({"status": "success", "count": len(self.sellers)})
        return response

    def _refresh_sellers(self) -> None:
        """
        Internal fucntion to retrieve a new list of sellers from the Nostr relay.
        The old list is discarded and the new list only contains unique sellers currently stored at the relay.

        Returns:
            List[NostrProfile]: List of Nostr profiles of all sellers.
        """
        sellers = self._nostr_client.retrieve_sellers()
        if len(sellers) == 0:
            self.logger.info("No sellers found")
        else:
            self.logger.info(f"Found {len(sellers)} sellers")

        # Print the locations of the sellers
        # for seller in sellers:
        #     print(f"Seller {seller.get_name()} has locations {seller.get_locations()}")

        self.sellers = sellers

    def _store_response_in_knowledge_base(self, response: str) -> None:
        doc = Document(
            id=str(uuid4()),
            content=response,
        )
        # print(f"Document length: {len(doc.content.split())} words")
        self.knowledge_base.load_documents([doc])  # Store response in Cassandra
