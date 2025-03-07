"""
Example FastAPI wrapper for the buyer agent.
"""

import asyncio
import logging
import uuid
import warnings

# from builtins import anext
from os import getenv
from pathlib import Path
from typing import AsyncGenerator, Iterator, Optional

import nest_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pgvector.sqlalchemy import Vector  # Correct import for vector storage
from pydantic import BaseModel
from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.sql import text

from agno.agent import Agent, AgentKnowledge, RunResponse  # type: ignore
from agno.embedder.openai import OpenAIEmbedder
from agno.models.openai import OpenAIChat  # type: ignore
from agno.vectordb.pgvector import PgVector, SearchType
from synvya_sdk import NostrKeys, Profile, generate_keys
from synvya_sdk.agno import BuyerTools

nest_asyncio.apply()
# Set logging to WARN level to suppress INFO logs
logging.basicConfig(level=logging.WARN)

# Configure logging first
logging.getLogger("cassandra").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning, module="cassandra")


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
NAME = "Snoqualmie Valley Chamber of Commerce"
DESCRIPTION = "Supporting the Snoqualmie Valley business community."
PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"
DISPLAY_NAME = "Snoqualmie Valley Chamber of Commerce"

# Initialize a buyer profile
profile = Profile(keys.get_public_key())
profile.set_name(NAME)
profile.set_about(DESCRIPTION)
profile.set_display_name(DISPLAY_NAME)
profile.set_picture(PICTURE)

# Initialize database connection
db_url = (
    f"postgresql+psycopg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(db_url)
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


reset_database()

vector_db = PgVector(
    table_name="sellers",
    db_url=db_url,
    schema="ai",
    search_type=SearchType.vector,
    embedder=OpenAIEmbedder(),
)

knowledge_base = AgentKnowledge(vector_db=vector_db)


buyer = Agent(  # type: ignore[call-arg]
    name="Virtual Guide for the Snoqualmie Valley",
    model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
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
    show_tool_calls=False,
    debug_mode=False,
    # async_mode=True,
    instructions=[
        """
        You're an AI assistant for people visiting a place. You will help them find
        things to do, places to go, and things to buy using exclusively the information
        provided by BuyerTools and stored in your knowledge base.
        
        When I ask you to refresh your sellers, use the refresh_sellers tool.
        
        Search the knowledge base for the most relevant information to the query before
        using the tools.
        
        When possible, connect multiple activities to create an itinerary. The itinerary
        can be for a few hours. It doesn't need to be a full day.

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


# === Define FastAPI app ===
app = FastAPI()


class QueryRequest(BaseModel):
    """
    Simple request model for the buyer agent.
    """

    query: str


async def async_wrapper(
    sync_iter: Iterator[RunResponse],
) -> AsyncGenerator[RunResponse, None]:
    """
    Wraps a synchronous iterator in an asynchronous generator.
    """
    while True:
        try:
            # Handle synchronous iterator in async context
            yield await asyncio.to_thread(next, sync_iter)
        except StopIteration:
            break
        except RuntimeError as e:
            if "StopIteration" in str(e):
                break
            raise


async def event_stream(
    response_stream: Iterator[RunResponse],
) -> AsyncGenerator[str, None]:
    """
    Streams the response from the buyer agent.
    """
    response_iter = async_wrapper(response_stream)
    first_chunk_event = asyncio.Event()

    async def fetch_first_chunk() -> Optional[RunResponse]:
        try:
            return await anext(response_iter)
        except StopAsyncIteration:
            first_chunk_event.set()
            return None
        finally:
            first_chunk_event.set()

    first_chunk_task = asyncio.create_task(fetch_first_chunk())

    # Heartbeat phase
    while not first_chunk_event.is_set():
        yield "Processing...\n"
        await asyncio.sleep(1)

    # Data streaming phase
    try:
        if first_response := await first_chunk_task:
            yield f"{first_response.get_content_as_string()}\n"

        async for response in response_iter:
            yield f"{response.get_content_as_string()}\n"

    except asyncio.CancelledError:
        print("Client disconnected")


@app.get("/")
def read_root() -> dict:
    """
    Simple health-check or root endpoint.
    """
    return {"message": "Hello from the Virtual Guide for the Snoqualmie Valley"}


@app.post("/query")
async def query_buyer(request: QueryRequest) -> StreamingResponse:
    """
    FastAPI endpoint to query the buyer agent and stream the response.
    """
    response_stream: Iterator[RunResponse] = buyer.run(request.query, stream=True)

    return StreamingResponse(
        event_stream(response_stream), media_type="text/event-stream"
    )
