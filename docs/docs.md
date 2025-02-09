# AgentStr Documentation

## Overview
AgentStr is a Python library that provides tools for interacting with Nostr marketplaces. The main components are the `Merchant` class and supporting data structures for managing stalls and products.

## Core Components

### Merchant Class
The `Merchant` class is a toolkit that allows merchants to manage their marketplace presence on Nostr. It handles:
- Profile management
- Stall management
- Product management
- Publishing and removing content from Nostr relays

#### Initialization
```python
merchant = Merchant(
    merchant_profile: Profile,  # Merchant's profile information
    relay: str,                # Nostr relay URL
    stalls: List[MerchantStall],   # List of stalls to manage
    products: List[MerchantProduct]  # List of products to sell
)
```

### Key Features

#### Profile Management
- `get_profile()`: Retrieves merchant profile in JSON format
- `publish_profile()`: Publishes merchant profile to Nostr

#### Stall Management
- `publish_stall_by_name(name: str)`: Publishes a specific stall
- `publish_all_stalls()`: Publishes all stalls
- `remove_stall_by_name(name: str)`: Removes a stall and its products
- `remove_all_stalls()`: Removes all stalls and their products

#### Product Management
- `publish_product_by_name(name: str)`: Publishes a specific product
- `publish_all_products()`: Publishes all products
- `publish_products_by_stall_name(stall_name: str)`: Publishes all products in a stall
- `remove_product_by_name(name: str)`: Removes a specific product
- `remove_all_products()`: Removes all products

### Data Structures

#### Profile
```python
Profile(
    name: str,      # Merchant's name
    about: str,     # Description
    picture: str,   # URL to profile picture
    nsec: str       # Optional private key
)
```

#### MerchantProduct
```python
MerchantProduct(
    id: str,
    stall_id: str,
    name: str,
    description: str,
    images: List[str],
    currency: str,
    price: float,
    quantity: int,
    shipping: List[ShippingCost],
    categories: Optional[List[str]],
    specs: Optional[List[List[str]]]
)
```

#### MerchantStall
```python
MerchantStall(
    id: str,
    name: str,
    description: str,
    currency: str,
    shipping: List[ShippingMethod]
)
```

### Function Return Values
All functions return JSON strings containing operation status and relevant information:

Success example:
```json
{
    "status": "success",
    "message": "Operation completed",
    "event_id": "event_id_here"
}
```

Error example:
```json
{
    "status": "error",
    "message": "Error description here"
}
```

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
from agentstr.marketplace import Merchant, Profile

# Create a merchant profile
profile = Profile(
    name="My Store",
    about="Best products ever",
    picture="https://example.com/pic.jpg"
)

# Initialize merchant
merchant = Merchant(profile, "wss://relay.example.com", stalls, products)

# Publish a stall
merchant.publish_stall_by_name("My Stall")

# Publish a product
merchant.publish_product_by_name("My Product")

# Remove a product
merchant.remove_product_by_name("My Product")
```

For more examples, check the `src/agentstr/examples/` directory in the repository.
