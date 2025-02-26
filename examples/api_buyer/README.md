# FastAPI Buyer Agent Example

This example creates a Docker container with a FastAPI API for the Basic Buyer Agent example found in examples/basic_buyer.

## Prerequisites

- PostgreSQL database with the pgvector extension installed.
- OpenAI API key.

## Setup
1. Clone the repository and navigate to this example:

```bash
git clone https://github.com/agentstr/agentstr.git
cd agentstr/examples/api_buyer
```

2. Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Keys:
- OPENAI_API_KEY=<your-openai-api-key sk-...>
- BUYER_AGENT_KEY=<your-buyer-agent-key nsec...>
- RELAY=<your-relay wss://...>
- DB_USERNAME=<your-db-username>
- DB_PASSWORD=<your-db-password>
- DB_HOST=<your-db-host>
- DB_PORT=<your-db-port>
- DB_NAME=<your-db-name>

You can skip the RELAY and BUYER_AGENT_KEY environment variables:
- The example will create a new private key for you and store it in the .env file for subsequent runs.
- The default relay wss://relay.damus.io will be used.

The username needs sufficient permissions to create the table in the database.

3. Build the Docker image and run the example:

```bash
docker build -t my-agent-app .
docker run -d -p 8000:8000 my-agent-app
```

## Usage

The API is now available at `http://localhost:8000/query` and you can inspect it at `http://localhost:8000/docs`.

 You can ask the buyer agent to:
 - Refresh the list of sellers from the relay
 - Find an specific seller by name or public key

 Ask the buyer agent `what tools do you have?` to see the available tools and their descriptions.