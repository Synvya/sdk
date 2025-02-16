# Basic Buyer Agent Example

This example demonstrates a complete setup of a buyer agent:
- Connects to a Nostr relay
- Retrieves a list of merchants from the relay
- Displays a list of merchants to the user
- Allows the user to select a merchant
- Displays a list of products from the selected merchant
- Allows the user to select a product
- Displays the product details to the user
- Interactive CLI interface

## Prerequisites

The buyer agent uses an a Cassandra vector database for Retrieval Augmented Generation (RAG).
   
Launch an instance of the Cassandra Docker official image locally before running the buyer agent.

```bash
docker run -d --name cassandra-db -p 9042:9042 cassandra:latest
```

## Setup
1. Clone the repository and navigate to this example:

```bash
git clone https://github.com/agentstr/agentstr.git
cd agentstr/examples/basic_buyer
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your keys:

If you don't have keys, just skip this step: 
- The example will create a new private key for you and store it in the .env file for subsequent runs.
- The default relay wss://relay.damus.io will be used.

```bash
cp .env.example .env
```

4. Run the example:

```bash
python basic_buyer.py
```

## Usage


 You can ask the buyer agent to:
 - Retrieve a list of sellers from the relay
 - Refresh the list of sellers from the relay
 - Find an specific seller by name or public key

 Ask the buyer agent `what tools do you have?` to see the available tools and their descriptions.