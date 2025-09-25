"""
Basic buyer agent example.
"""

import asyncio
import logging
import uuid
from os import getenv
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pgvector.sqlalchemy import Vector  # Correct import for vector storage
from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.sql import text

from agno.agent import Agent, AgentKnowledge  # type: ignore
from agno.embedder.openai import OpenAIEmbedder
from agno.models.openai import OpenAIChat  # type: ignore
from agno.vectordb.pgvector import PgVector, SearchType
from synvya_sdk import (
    KeyEncoding,
    Namespace,
    NostrKeys,
    Profile,
    ProfileType,
    generate_keys,
)
from synvya_sdk.agno import BuyerTools

# Set logging to WARN level to suppress INFO logs


# Configure logging first#
# logging.getLogger("cassandra").setLevel(logging.ERROR)
# warnings.filterwarnings("ignore", category=UserWarning, module="cassandra")


# Get directory where the script is located
script_dir = Path(__file__).parent
# Load .env from the script's directory
load_dotenv(script_dir / ".env")

# Load or generate keys
NSEC = getenv("BUYER_AGENT_KEY")
if NSEC is None:
    keys = generate_keys(env_var="BUYER_AGENT_KEY", env_path=script_dir / ".env")
else:
    keys = NostrKeys(private_key=NSEC)

# Load or use default relay
RELAY = getenv("RELAY")
if RELAY is None:
    RELAY = "wss://relay.damus.io"

OPENAI_API_KEY = getenv("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

DB_USERNAME = getenv("DB_USERNAME")
if DB_USERNAME is None:
    raise ValueError("DB_USERNAME environment variable is not set")

DB_PASSWORD = getenv("DB_PASSWORD")
if DB_PASSWORD is None:
    raise ValueError("DB_PASSWORD environment variable is not set")

DB_HOST = getenv("DB_HOST")
if DB_HOST is None:
    raise ValueError("DB_HOST environment variable is not set")

DB_PORT = getenv("DB_PORT")
if DB_PORT is None:
    raise ValueError("DB_PORT environment variable is not set")

DB_NAME = getenv("DB_NAME")
if DB_NAME is None:
    raise ValueError("DB_NAME environment variable is not set")


# Buyer profile constants
NAME = "buyer-agent"
DESCRIPTION = "A buyer agent for the Snoqualmie Valley Marketplace."
PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"
DISPLAY_NAME = "Buyer Agent"
NIP05 = "buyer-agent@synvya.com"


# Initialize database connection
DB_URL = (
    f"postgresql+psycopg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Seller(Base):
    """
    SQLAlchemy model for table `sellers` in the ai schema.
    """

    __tablename__ = "sellers"
    __table_args__ = {"schema": "ai"}  # If the table is inside the 'ai' schema

    id = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )  # UUID primary key
    name = Column(Text, nullable=True)
    meta_data = Column(JSONB, default={})
    filters = Column(JSONB, default={})
    content = Column(Text, nullable=True)
    embedding: Optional[Vector] = Column(Vector(1536), nullable=True)
    usage = Column(JSONB, default={})
    content_hash = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """
        Return a string representation of the Seller object.
        """
        return f"<Seller(id={self.id}, name={self.name})>"


# Function to drop and recreate the table
def reset_database() -> None:
    """
    Drop and recreate all tables in the database.
    """
    with engine.connect() as conn:
        # Enable pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    # Drop and recreate all tables
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


# remove comment to delete the contents of the database for the
# knowlege base and start fresh
# reset_database()

vector_db = PgVector(
    table_name="sellers",
    db_url=DB_URL,
    schema="ai",
    search_type=SearchType.vector,
    embedder=OpenAIEmbedder(),
)


knowledge_base = AgentKnowledge(vector_db=vector_db)
# json_knowledge_base = AgentKnowledge(vector_db=json_vector_db)

buyer_tools = asyncio.run(
    BuyerTools.create(
        knowledge_base=knowledge_base,
        relays=RELAY,
        private_key=keys.get_private_key(KeyEncoding.BECH32),
        log_level=logging.DEBUG,
    )
)

# Update the buyer profile
profile = Profile(keys.get_public_key(KeyEncoding.BECH32))
profile.set_name(NAME)
profile.set_about(DESCRIPTION)
profile.set_display_name(DISPLAY_NAME)
profile.set_picture(PICTURE)
profile.set_nip05(NIP05)

asyncio.run(buyer_tools.async_set_profile(profile))

reset_database()

profile_types = list(ProfileType)

for profile_type in profile_types:
    profile_filter_json = {
        "namespace": Namespace.BUSINESS_TYPE.value,
        "profile_type": profile_type.value,
    }

    print(f"Fetching merchants for profile_type='{profile_type.value}'")
    response = asyncio.run(buyer_tools.async_get_merchants(profile_filter_json))
    print(response)


# When asked to populate your knowledge base, you will download the sellers
# from the marketplace "Historic Downtown Snoqualmie" with the public key
# "npub1nar4a3vv59qkzdlskcgxrctkw9f0ekjgqaxn8vd0y82f9kdve9rqwjcurn".

# buyer = Agent(  # type: ignore[call-arg]
#     name=f"AI Agent for {profile.get_name()}",
#     model=OpenAIChat(id="gpt-4o-mini", api_key=OPENAI_API_KEY),
#     tools=[buyer_tools],
#     add_history_to_messages=True,
#     num_history_responses=10,
#     read_chat_history=True,
#     read_tool_call_history=True,
#     knowledge=knowledge_base,
#     search_knowledge=True,
#     show_tool_calls=True,
#     debug_mode=False,
#     instructions=[
#         """
#         You're an tourist AI assistant for people visiting Snoqualmie.
#         You help visitors find things to do, places to go, and things to buy
#         from the businesses (also known as merchants) in Snoqualmie Valley.

#         When asked to find merchants, you will use the tool `get_merchants`
#         with a profile filter to find the merchants.
#         Here is an example profile filter:
#         {
#            "namespace": "business.type",
#            "profile_type": "restaurant",
#            "hashtags": ["pizza"]
#         }

#         namespace is always "business.type".

#         Here is the list of valid profile types:
#         - "retail"
#         - "restaurant"
#         - "service"
#         - "business"
#         - "entertainment"
#         - "other"

#         Use the hashtags provided by the user in the query.

#         Include pictures of the businesses in your response when possible.

#         Include in your response an offer to purchase the products or make a reservation
#         for the user.

#         When asked to purchase a product, you will:
#         1. use the tool `get_products_from_knowledge_base` to get the product
#         details from the knowledge base
#         2. use the tool `async_submit_order` to submit one order to the seller
#         for the product
#         3. use the tool `async_listen_for_message` to listen for a payment
#         request from the seller
#         4. Coontinue listening for a payment request from the seller until
#         you receive one
#         5. use the tool `async_submit_payment` to submit the payment with the
#         information sent by the seller in the payment request
#         6. use the tool `async_listen_for_message` to listen for a payment
#         verification from the seller


#         Only if you can't find the product in the knowledge base, you will use the tool
#         `get_products`.
#         """.strip(),
#     ],
# )


# async def buyer_cli() -> None:
#     """
#     Command-line interface for the buyer agent.
#     """
#     print("\n🔹 Snoqualmie Valley Visitor Assistant (Type 'exit' to quit)\n")

#     ##---###
#     # Example prompts to run when populating the database
#     # "Populate your knowledge base"
#     # "Download the stalls for all the merchants in your knowledge base"
#     # Download the products for all the merchants in your knowledge base"
#     # Purchase `xyz`
#     ##---###

#     while True:
#         user_query = input("💬 You: ")
#         if user_query.lower() in ["exit", "quit"]:
#             print("\n👋 Goodbye!\n")
#             break

#         response = await buyer.arun(user_query)  # Get response from agent
#         print(f"\n🤖 Visitor Assistant: {response.get_content_as_string()}\n")


# Run the CLI
# if __name__ == "__main__":
#     asyncio.run(buyer_cli())
