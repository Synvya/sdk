"""
Example FastAPI wrapper for the buyer agent.
"""

import datetime
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

# from builtins import anext
from os import getenv
from pathlib import Path
from typing import List, Literal, Optional, Union

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, Field
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


# Add the filter code here
class EndpointFilter(logging.Filter):
    def __init__(self, path: str) -> None:
        self.path = path

    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find(f"GET {self.path}") == -1


# Configure the filter
logging.getLogger("uvicorn.access").addFilter(EndpointFilter("/health"))

# Set logging to WARN level to suppress INFO logs
logging.basicConfig(level=logging.WARN)


# Load environment variables from .env
script_dir = Path(__file__).parent
load_dotenv(script_dir / ".env")

NSEC = getenv("BUYER_AGENT_KEY")

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
NAME = "snovalley"
ABOUT = "Supporting the Snoqualmie Valley business community."
PICTURE = "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png"
DISPLAY_NAME = "Snoqualmie Valley Chamber of Commerce"
WEBSITE = "https://www.snovalley.org"
# Initialize a buyer profile


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
    Drop and recreate all tables and schema in the database.
    """
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS ai;"))
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)


if getenv("RESET_DATABASE", "").lower() in ("true", "1", "yes"):
    print("Resetting database...")
    reset_database()
    print("Database reset complete.")

INSTRUCTIONS = """
    You're an tourist AI assistant for people visiting Snoqualmie.
    You help visitors find things to do, places to go, and things to buy
    from the businesses (also known as merchants) in Snoqualmie Valley.

    When asked to find merchants, you will use the tool `async_get_merchants` with a profile
    filter to find the merchants.
    Here is an example profile filter:
    {"namespace": "com.synvya.merchant", "profile_type": "restaurant", "hashtags": ["pizza"]}

    namespace is always "com.synvya.merchant".

    Here is the list of valid profile types:
    - "retail"
    - "restaurant"
    - "service"
    - "business"
    - "entertainment"
    - "other"

    Use the hashtags provided by the user in the query.

    Include pictures of the businesses in your response when possible.

    For the merchants you find, download their products with `async_get_products`.

    Include in your response an offer to purchase the products or make a reservation
    for the user.

    When asked to purchase a product, you will:
    1. use the tool `get_products_from_knowledge_base` to get the product details from
    the knowledge base. If you can't find the product in the knowledge base, then use the
    tool `async_get_products` to donwload the products from Nostr
    2. use the tool `async_submit_order` to submit one order to the seller for the product
    3. use the tool `async_listen_for_message` to listen for a payment request from the seller
    4. Continue listening for a payment request from the seller until you receive one
    5. use the tool `async_submit_payment` to submit the payment with the information sent by
    the seller in the payment request
    6. use the tool `async_listen_for_message` to listen for a payment verification from the seller.
    """.strip()


# === Define FastAPI app ===
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Initialize SDK client and other async-related setup here

    if NSEC is None:
        keys = generate_keys(env_var="BUYER_AGENT_KEY", env_path=script_dir / ".env")
    else:
        keys = NostrKeys.from_private_key(NSEC)

    RELAY = getenv("RELAY") or "wss://relay.damus.io"

    profile = Profile(keys.get_public_key())
    profile.set_name(NAME)
    profile.set_about(ABOUT)
    profile.set_display_name(DISPLAY_NAME)
    profile.set_picture(PICTURE)
    profile.set_website(WEBSITE)
    profile.set_nip05(f"{NAME}@synvya.com")

    vector_db = PgVector(
        table_name="sellers",
        db_url=db_url,
        schema="ai",
        search_type=SearchType.vector,
        embedder=OpenAIEmbedder(),
    )

    knowledge_base = AgentKnowledge(vector_db=vector_db)

    app.state.buyer_tools = await BuyerTools.create(
        knowledge_base=knowledge_base,
        relays=RELAY,
        private_key=keys.get_private_key(),
        log_level=logging.DEBUG,
    )

    await app.state.buyer_tools.async_set_profile(profile)

    app.state.buyer = Agent(
        name="Virtual Guide for the Snoqualmie Valley",
        model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
        tools=[app.state.buyer_tools],
        add_history_to_messages=True,
        num_history_responses=10,
        read_chat_history=True,
        read_tool_call_history=True,
        knowledge=knowledge_base,
        show_tool_calls=True,
        debug_mode=False,
        instructions=[INSTRUCTIONS],
    )

    yield  # Lifespan context manager ends here


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "https://client-web.synvya.com",
        "https://97cddff9-ccce-4cf8-93ff-1a55031a33f1.lovableproject.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Origin", "Accept", "X-Requested-With"],
)


class QueryRequest(BaseModel):
    """
    Simple request model for the buyer agent.
    """

    query: str


class ImageContent(BaseModel):
    """Model for image content"""

    type: Literal["image"] = "image"
    url: str
    alt_text: str
    caption: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class TextContent(BaseModel):
    """Model for text content"""

    type: Literal["text"] = "text"
    text: str


class CompleteChatResponse(BaseModel):
    """Model for complete chat responses with rich content"""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    content: List[Union[TextContent, ImageContent]]
    query: str


@app.get("/health")
def health_check() -> dict:
    """
    Simple health-check endpoint.
    """
    return {"message": "Hello from the Virtual Guide for the Snoqualmie Valley"}


@app.post("/chat")
async def chat(request: QueryRequest, fastapi_request: Request) -> CompleteChatResponse:
    """
    Query the buyer agent and return a complete structured response
    with possible image content.
    """
    try:
        # Run in non-streaming mode
        response = await app.state.buyer.arun(request.query, stream=False)

        # Get text content
        text_content = response.get_content_as_string()

        # Extract image URLs if present
        content_parts: List[Union[TextContent, ImageContent]] = []

        # Example of extracting image references from text (very simplified)
        # In a real implementation, your LLM would provide structured data about images
        if "![" in text_content and "](" in text_content:
            # Simple markdown image syntax detection
            parts = text_content.split("![")

            # Add initial text if any
            if parts[0]:
                content_parts.append(TextContent(text=parts[0]))

            # Process each image and text after it
            for part in parts[1:]:
                if "](" in part:
                    alt_end = part.index("](")
                    url_end = part.index(")", alt_end)

                    alt_text = part[:alt_end]
                    url = part[alt_end + 2 : url_end]

                    # Add the image
                    content_parts.append(
                        ImageContent(url=url, alt_text=alt_text, caption=alt_text)
                    )

                    # Add text after the image if any
                    if url_end + 1 < len(part):
                        content_parts.append(TextContent(text=part[url_end + 1 :]))
        else:
            # No images, just text
            content_parts.append(TextContent(text=text_content))

        return CompleteChatResponse(content=content_parts, query=request.query)
    except Exception as e:
        logging.error("Error generating response: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
