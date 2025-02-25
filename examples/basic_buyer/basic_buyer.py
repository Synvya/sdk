"""
Basic buyer agent example.
"""

import logging
import warnings
from os import getenv
from pathlib import Path

from agno.agent import Agent, AgentKnowledge  # type: ignore
from agno.embedder.openai import OpenAIEmbedder
from agno.models.openai import OpenAIChat  # type: ignore

# from agno.vectordb.cassandra import Cassandra
from agno.vectordb.pgvector import PgVector, SearchType

# from cassandra.cluster import Cluster
# from cassandra.policies import RoundRobinPolicy
from dotenv import load_dotenv

from agentstr import AgentProfile, BuyerTools, Keys, generate_and_save_keys

# Set logging to WARN level to suppress INFO logs
logging.basicConfig(level=logging.WARN)

# Configure logging first
logging.getLogger("cassandra").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning, module="cassandra")


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
NSEC = getenv(ENV_KEY)
if NSEC is None:
    keys = generate_and_save_keys(env_var=ENV_KEY, env_path=script_dir / ".env")
else:
    keys = Keys.parse(NSEC)


# Load or use default relay
RELAY = getenv(ENV_RELAY)
if RELAY is None:
    RELAY = DEFAULT_RELAY

OPENAI_API_KEY = getenv("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not set")
# print(f"OpenAI API key: {openai_api_key}")

# Initialize a buyer profile
profile = AgentProfile(keys=keys)
profile.set_name(NAME)
profile.set_about(DESCRIPTION)
profile.set_display_name(DISPLAY_NAME)
profile.set_picture(PICTURE)

# Initialize Cluster with recommended settings
# cluster = Cluster(
#     ["127.0.0.1"],
#     port=9042,
#     protocol_version=5,  # Verify your Cassandra version
#     load_balancing_policy=RoundRobinPolicy(),
# )

# session = cluster.connect()

# # Create the keyspace
# session.execute(
#     """
#     CREATE KEYSPACE IF NOT EXISTS synvya
#     WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 }
#     """
# )

# # Drop existing table (if needed)
# session.execute("DROP TABLE IF EXISTS synvya.sellers")

# # Create the table with 1536-dimensional vector for OpenAI
# session.execute(
#     """
#     CREATE TABLE synvya.sellers (
#         row_id text PRIMARY KEY,
#         attributes_blob text,
#         body_blob text,
#         document_name text,
#         vector vector<float, 1536>,
#         metadata_s map<text, text>
#     ) WITH additional_write_policy = '99p'
#       AND allow_auto_snapshot = true
#       AND bloom_filter_fp_chance = 0.01
#       AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
#       AND cdc = false
#       AND comment = ''
#       AND compaction = {
#           'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy',
#           'max_threshold': '32',
#           'min_threshold': '4'
#       }
#       AND compression = {
#           'chunk_length_in_kb': '16',
#           'class': 'org.apache.cassandra.io.compress.LZ4Compressor'
#       }
#       AND memtable = 'default'
#       AND crc_check_chance = 1.0
#       AND default_time_to_live = 0
#       AND extensions = {}
#       AND gc_grace_seconds = 864000
#       AND incremental_backups = true
#       AND max_index_interval = 2048
#       AND memtable_flush_period_in_ms = 0
#       AND min_index_interval = 128
#       AND read_repair = 'BLOCKING'
#       AND speculative_retry = '99p';
#     """
# )

# knowledge_base = AgentKnowledge(
#     vector_db=Cassandra(
#         table_name="sellers",
#         keyspace="synvya",
#         session=session,
#         embedder=OpenAIEmbedder(),
#     ),
# )

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
vector_db = PgVector(
    table_name="sellers",
    db_url=db_url,
    search_type=SearchType.vector,
    embedder=OpenAIEmbedder(),
)

knowledge_base = AgentKnowledge(vector_db=vector_db)


buyer = Agent(  # type: ignore[call-arg]
    name=f"AI Agent for {profile.get_name()}",
    model=OpenAIChat(id="gpt-4o-mini", api_key=OPENAI_API_KEY),
    tools=[
        BuyerTools(knowledge_base=knowledge_base, buyer_profile=profile, relay=RELAY)
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
        """
        You're an AI assistant for people visiting a place. You will
        help them find things to do, places to go, and things to buy
        using exclusively the information provided by BuyerTools and
        stored in your knowledge base.
        
        When I ask you to refresh your sellers, use the refresh_sellers tool.
        
        Search the knowledge base for the most relevant information to
        the query before using the tools.
        
        When possible, connect multiple activities to create an itinerary.
        The itinerary can be for a few hours. It doesn't need to be a full day.

        After using the tool find_sellers_by_location, always immediately call the tool 
        get_seller_products to retrieve the products from the merchants in that location
        and include the products in the itinerary.
        
        Only include in the itinerary merchants that are in your knowledge base.
                
        When including merchants from your knowledge base in your response, make sure to 
        include their products and services in the itinerary with the current times
        based on product information. Provide also the price of the products and
        services.
        Offer to purchase the products or make a reservation and then include
        this in your overall response.
        """.strip(),
    ],
)


def buyer_cli() -> None:
    """
    Command-line interface for the buyer agent.
    """
    print("\n🔹 Snoqualmie Valley Visitor Assistant (Type 'exit' to quit)\n")
    while True:
        user_query = input("💬 You: ")
        if user_query.lower() in ["exit", "quit"]:
            print("\n👋 Goodbye!\n")
            break

        response = buyer.run(user_query)  # Get response from agent
        print(f"\n🤖 Visitor Assistant: {response.get_content_as_string()}\n")


# Run the CLI
buyer_cli()
