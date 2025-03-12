"""
Basic buyer agent example.
"""

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
from synvya_sdk import NostrKeys, Profile, generate_keys
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
    keys = NostrKeys.from_private_key(NSEC)

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
NAME = "Business Name Inc."
DESCRIPTION = "I'm in the business of doing business."
PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"
DISPLAY_NAME = "Buyer Agent for Business Name Inc."
# Initialize a buyer profile
profile = Profile(keys.get_public_key())
profile.set_name(NAME)
profile.set_about(DESCRIPTION)
profile.set_display_name(DISPLAY_NAME)
profile.set_picture(PICTURE)

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


# class Json(Base):
#     """
#     SQLAlchemy model for table `json` in the ai schema.
#     """

#     __tablename__ = "json"
#     __table_args__ = {"schema": "ai"}  # If the table is inside the 'ai' schema

#     id = Column(
#         String, primary_key=True, default=lambda: str(uuid.uuid4())
#     )  # UUID primary key
#     name = Column(Text, nullable=True)
#     meta_data = Column(JSONB, default={})
#     filters = Column(JSONB, default={})
#     content = Column(JSONB, nullable=False)
#     embedding: Optional[Vector] = Column(Vector(1536), nullable=True)
#     usage = Column(JSONB, default={})
#     content_hash = Column(Text, nullable=True)

#     def __repr__(self) -> str:
#         """
#         Return a string representation of the Json object.
#         """
#         return f"<Json(id={self.id}, name={self.name})>"


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


# reset_database()

vector_db = PgVector(
    table_name="sellers",
    db_url=DB_URL,
    schema="ai",
    search_type=SearchType.vector,
    embedder=OpenAIEmbedder(),
)

# json_vector_db = PgVector(
#     table_name="json",
#     db_url=DB_URL,
#     schema="ai",
#     search_type=SearchType.vector,
#     embedder=OpenAIEmbedder(),
# )


knowledge_base = AgentKnowledge(vector_db=vector_db)
# json_knowledge_base = AgentKnowledge(vector_db=json_vector_db)


buyer = Agent(  # type: ignore[call-arg]
    name=f"AI Agent for {profile.get_name()}",
    model=OpenAIChat(id="gpt-4o-mini", api_key=OPENAI_API_KEY),
    tools=[
        BuyerTools(
            knowledge_base=knowledge_base,
            relay=RELAY,
            private_key=keys.get_private_key(),
        )
    ],
    add_history_to_messages=True,
    num_history_responses=10,
    read_chat_history=True,
    read_tool_call_history=True,
    knowledge=knowledge_base,
    search_knowledge=True,
    show_tool_calls=True,
    debug_mode=False,
    # async_mode=True,
    instructions=[
        """
        You're an tourist AI assistant for people visiting Snoqualmie.
        You help visitors find things to do, places to go, and things to buy
        from the businesses (also known as sellers) in the Historic Downtown
        Snoqualmie using exclusively the information stored in your knowledge base.

        When asked to populate your knowledge base, you will download the sellers
        from the marketplace "Historic Downtown Snoqualmie" with the public key
        "npub1nar4a3vv59qkzdlskcgxrctkw9f0ekjgqaxn8vd0y82f9kdve9rqwjcurn".
        
        Under no circumstances use the tool `download_all_sellers` from BuyerTools.
        
        Once you're done with these steps, you will answer questions from the user with 
        the information stored in your knowledge base.

        Only provide information about the businesses that are in your knowledge base.

        Include pictures of the businesses in your response when possible.

        Include in your response an offer to purchase the products or make a reservation
        for the user.
        """.strip(),
    ],
)


def buyer_cli() -> None:
    """
    Command-line interface for the buyer agent.
    """
    print("\n🔹 Snoqualmie Valley Visitor Assistant (Type 'exit' to quit)\n")

    # print("Downloading sellers from Snoqualmie Valley Marketplace...")
    # response = buyer.run("populate your knowledge base")
    # print(f"\n🤖 Visitor Assistant: {response.get_content_as_string()}\n")

    # print("Downloading stalls from all sellers...")
    # response = buyer.run("download the stalls from all sellers in your knowledge base")
    # print(f"\n🤖 Visitor Assistant: {response.get_content_as_string()}\n")

    # print("Downloading products from all sellers...")
    # response = buyer.run(
    #     "download the products from all sellers in your knowledge base"
    # )
    # print(f"\n🤖 Visitor Assistant: {response.get_content_as_string()}\n")

    while True:
        user_query = input("💬 You: ")
        if user_query.lower() in ["exit", "quit"]:
            print("\n👋 Goodbye!\n")
            break

        response = buyer.run(user_query)  # Get response from agent
        print(f"\n🤖 Visitor Assistant: {response.get_content_as_string()}\n")


# Run the CLI
buyer_cli()
