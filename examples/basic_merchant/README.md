    # Basic Merchant Agent Example

    This example demonstrates a complete setup of a merchant agent with:
    - Multiple stalls (Hardware Store and Trade School)
    - Multiple products per stall
    - Different shipping zones and costs
    - Interactive CLI interface

    ## Setup

    1. Clone the repository and navigate to this example:

    ```bash
    git clone https://github.com/agentstr/agentstr.git
    cd agentstr/examples/basic_merchant
    ```

    2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

    3. Copy `.env.example` to `.env` and fill in your keys:

    ```bash
    cp .env.example .env
    ```

    4. Run the example:

    ```bash
    python basic_merchant.py
    ```

## Usage

You can skip the RELAY and NSEC_BASIC_MERCHANT_KEY environment variables from the .env file:
 - The example will create a new private key for you and store it in the .env file for subsequent runs.
 - The default relay wss://relay.damus.io will be used.

You can ask the merchant agent to:
- List all stalls and products
- List all products from a specific stall
- Publish stalls and products to Nostr
- Remove stalls and products from Nostr
