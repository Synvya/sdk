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

The buyer agent uses an a Postgres database with pgvector extension for Retrieval Augmented Generation (RAG).
   
Download and launch on your computer an instance of the pgvector Docker image before running the buyer agent.

```bash
docker run -d \
  -e POSTGRES_DB=ai \
  -e POSTGRES_USER=synvya \
  -e POSTGRES_PASSWORD=synvya \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -v pgvolume:/var/lib/postgresql/data \
  -p 5532:5432 \
  --name pgvector \
  pgvector/pgvector:pg17

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

You can skip the RELAY and BUYER_AGENT_KEY environment variables from the .env file:
- The example will create a new private key for you and store it in the .env file for subsequent runs.
- The default relay wss://relay.damus.io will be used.

You WILL need an OpenAI API key.

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