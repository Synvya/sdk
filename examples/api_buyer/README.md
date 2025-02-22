# FastAPI Buyer Agent Example

This example creates a Docker Compose Stack with two containers:
- A Docker container with a FastAPI API for the Basic Buyer Agent example found in examples/basic_buyer.
- A Docker container with a Cassandra database.

## Setup
1. Clone the repository and navigate to this example:

```bash
git clone https://github.com/agentstr/agentstr.git
cd agentstr/examples/api_buyer
```

2. Copy `.env.example` to `.env` and fill in your keys:

You can skip the RELAY and BUYER_AGENT_KEY environment variables from the .env file:
- The example will create a new private key for you and store it in the .env file for subsequent runs.
- The default relay wss://relay.damus.io will be used.

You WILL need an OpenAI API key.


```bash
cp .env.example .env
```

4. Run the example:

```bash
docker-compose up --build
```

## Usage


 You can ask the buyer agent to:
 - Retrieve a list of sellers from the relay
 - Refresh the list of sellers from the relay
 - Find an specific seller by name or public key

 Ask the buyer agent `what tools do you have?` to see the available tools and their descriptions.