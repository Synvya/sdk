# AgentStr Documentation

## Overview
AgentStr is a Python library that provides tools for interacting with Nostr marketplaces. The main components are the `MerchantTools` class, the `BuyerTools` class, and supporting data structures for managing stalls and products.

## Core Components

### MerchantTools Class
The `MerchantTools` class is a toolkit that allows merchants to manage their marketplace presence on Nostr. It handles:
- Profile management
- Stall management
- Product management
- Publishing and removing content from Nostr relays

#### Initialization
```python
merchant_tools = MerchantTools(
    merchant_profile: AgentProfile,  # Merchant's profile information
    relay: str,                     # Nostr relay URL
    stalls: List[MerchantStall],    # List of stalls to manage
    products: List[MerchantProduct] # List of products to sell
)
```

#### Key Features

- `get_profile()`: Retrieves merchant profile in JSON format
- `get_relay()`: Retrieves the relay URL
- `get_products()`: Retrieves all products
- `get_stalls()`: Retrieves all stalls
- `publish_all_products()`: Publishes all products
- `publish_all_stalls()`: Publishes all stalls
- `publish_new_product(product: MerchantProduct)`: Publishes a new product
- `publish_product_by_name(product_name: str)`: Publishes a specific product by name
- `publish_products_by_stall_name(stall_name: str)`: Publishes all products in a stall
- `publish_profile()`: Publishes merchant profile to Nostr
- `publish_new_stall(stall: MerchantStall)`: Publishes a new stall
- `publish_stall_by_name(stall_name: str)`: Publishes a specific stall by name
- `remove_all_products()`: Removes all products
- `remove_all_stalls()`: Removes all stalls
- `remove_product_by_name(product_name: str)`: Removes a specific product by name
- `remove_stall_by_name(stall_name: str)`: Removes a specific stall by name
- `get_event_id(response: Any)`: Retrieves the event ID from a response

### BuyerTools Class
The `BuyerTools` class provides functionalities for buyers to interact with sellers on Nostr. It handles:
- Seller discovery
- Profile retrieval
- Product and collection management

#### Initialization
```python
buyer_tools = BuyerTools(
    knowledge_base: AgentKnowledge,  # Buyer's knowledge base
    buyer_profile: AgentProfile,     # Buyer's profile information
    relay: str                       # Nostr relay URL
)
```

#### Key Features

- `find_seller_by_name(name: str)`: Finds a seller by name
- `find_seller_by_public_key(public_key: str)`: Finds a seller by public key
- `find_sellers_by_location(location: str)`: Finds sellers by location
- `get_profile()`: Retrieves buyer profile in JSON format
- `get_relay()`: Retrieves the relay URL
- `get_seller_collections(public_key: str)`: Retrieves collections from a seller
- `get_seller_count()`: Retrieves the count of sellers
- `get_seller_products(public_key: str)`: Retrieves products from a seller
- `get_sellers()`: Retrieves all sellers
- `purchase_product(product: str)`: Purchases a product
- `refresh_sellers()`: Refreshes the list of sellers
- `_refresh_sellers()`: Internal method to refresh sellers
- `_store_response_in_knowledge_base(response: str)`: Stores a response in the knowledge base

### Important Notes

1. **Event IDs**: When content is published to Nostr, event IDs are stored in the local database. These IDs are required for updating or removing content later.

2. **Local Database**: The Merchant class maintains two local databases:
   - `product_db`: List of tuples containing (MerchantProduct, EventId)
   - `stall_db`: List of tuples containing (MerchantStall, EventId)

3. **Argument Formats**: Functions that take names as arguments accept multiple formats:
   - Direct string: `"my_product"`
   - JSON string: `'{"name": "my_product"}'`
   - Dict object: `{"name": "my_product"}`

4. **Removal Operations**: When removing content:
   - Items are only removed from Nostr, not from local database
   - Event IDs are cleared but products/stalls remain in database
   - Products in a stall are removed before the stall itself

5. **Error Handling**: All operations include proper error handling and return descriptive status messages in JSON format.

## Examples

### Basic Usage
```python
from agentstr.marketplace import MerchantTools, Profile

# Create a merchant profile
profile = Profile(
    name="My Store",
    about="Best products ever",
    picture="https://example.com/pic.jpg"
)

# Initialize merchant tools
merchant_tools = MerchantTools(profile, "wss://relay.example.com", stalls, products)

# Publish a stall
merchant_tools.publish_stall_by_name("My Stall")

# Publish a product
merchant_tools.publish_product_by_name("My Product")

# Remove a product
merchant_tools.remove_product_by_name("My Product")
```

For more examples, check the `src/agentstr/examples/` directory in the repository.
