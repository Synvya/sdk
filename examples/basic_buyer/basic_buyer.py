import logging
from os import getenv
from pathlib import Path
from uuid import uuid4

from agno.agent import Agent, AgentKnowledge  # type: ignore
from agno.document.base import Document
from agno.embedder.openai import OpenAIEmbedder
from agno.models.openai import OpenAIChat  # type: ignore
from agno.vectordb.cassandra import Cassandra
from cassandra.cluster import Cluster
from dotenv import load_dotenv

from agentstr.buyer import BuyerTools
from agentstr.models import AgentProfile
from agentstr.nostr import Keys, generate_and_save_keys

# Set logging to WARN level to suppress INFO logs
logging.basicConfig(level=logging.WARN)


# Environment variables
ENV_RELAY = "RELAY"
DEFAULT_RELAY = "wss://relay.damus.io"
ENV_KEY = "BUYER_AGENT_KEY"

# Buyer profile constants
NAME = "Business Name Inc."
DESCRIPTION = "I'm in the business of doing business."
PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"
DISPLAY_NAME = "Buyer Agent for Business Name Inc."

# Get directory where the script is located
script_dir = Path(__file__).parent
# Load .env from the script's directory
load_dotenv(script_dir / ".env")

# Load or generate keys
nsec = getenv(ENV_KEY)
if nsec is None:
    keys = generate_and_save_keys(env_var=ENV_KEY, env_path=script_dir / ".env")
else:
    keys = Keys.parse(nsec)


# Load or use default relay
relay = getenv(ENV_RELAY)
if relay is None:
    relay = DEFAULT_RELAY

openai_api_key = getenv("OPENAI_API_KEY")
if openai_api_key is None:
    raise ValueError("OPENAI_API_KEY is not set")
# print(f"OpenAI API key: {openai_api_key}")

# Initialize a buyer profile
profile = AgentProfile(keys=keys)
profile.set_name(NAME)
profile.set_about(DESCRIPTION)
profile.set_display_name(DISPLAY_NAME)
profile.set_picture(PICTURE)

# Set up Cassandra DB

cluster = Cluster(["127.0.0.1"], port=9042)

session = cluster.connect()

# Create the keyspace
session.execute(
    """
    CREATE KEYSPACE IF NOT EXISTS synvya
    WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 }
    """
)

# Drop existing table (if needed)
session.execute("DROP TABLE IF EXISTS synvya.sellers")

# Create the table with 1536-dimensional vector for OpenAI
session.execute(
    """
    CREATE TABLE synvya.sellers (
        row_id text PRIMARY KEY,
        attributes_blob text,
        body_blob text,
        document_name text,
        vector vector<float, 1536>,
        metadata_s map<text, text>
    ) WITH additional_write_policy = '99p'
      AND allow_auto_snapshot = true
      AND bloom_filter_fp_chance = 0.01
      AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
      AND cdc = false
      AND comment = ''
      AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy', 'max_threshold': '32', 'min_threshold': '4'}
      AND compression = {'chunk_length_in_kb': '16', 'class': 'org.apache.cassandra.io.compress.LZ4Compressor'}
      AND memtable = 'default'
      AND crc_check_chance = 1.0
      AND default_time_to_live = 0
      AND extensions = {}
      AND gc_grace_seconds = 864000
      AND incremental_backups = true
      AND max_index_interval = 2048
      AND memtable_flush_period_in_ms = 0
      AND min_index_interval = 128
      AND read_repair = 'BLOCKING'
      AND speculative_retry = '99p';
    """
)


knowledge_base = AgentKnowledge(
    vector_db=Cassandra(
        table_name="sellers",
        keyspace="synvya",
        session=session,
        embedder=OpenAIEmbedder(),
    ),
)


buyer = Agent(  # type: ignore[call-arg]
    name=f"AI Agent for {profile.get_name()}",
    model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
    tools=[
        BuyerTools(knowledge_base=knowledge_base, buyer_profile=profile, relay=relay)
    ],
    add_history_to_messages=True,
    num_history_responses=10,
    read_chat_history=True,
    read_tool_call_history=True,
    knowledge=knowledge_base,
    show_tool_calls=False,
    debug_mode=False,
    # async_mode=True,
    instructions=[
        """Search the knowledge base for the most relevant information to the query before using the tools.
        """.strip(),
    ],
)


# Command-line interface with response storage
def buyer_cli() -> None:
    print("\n🔹 Buyer Agent CLI (Type 'exit' to quit)\n")
    while True:
        user_query = input("💬 You: ")
        if user_query.lower() in ["exit", "quit"]:
            print("\n👋 Exiting Buyer Agent CLI. Goodbye!\n")
            break

        response = buyer.run(user_query)  # Get response from agent
        print(f"\n🤖 Buyer Agent: {response.get_content_as_string()}\n")


# Run the CLI
buyer_cli()

# buyer.print_response("List the products of the merchant")
# buyer.cli_app(stream=False)
