from dotenv import load_dotenv
from qdrant_client.models import (
    PointStruct,
    Distance,
    ScalarQuantization,
    VectorParams,
    Distance,
    ScalarQuantizationConfig,
    HnswConfigDiff,
    VectorParams,
    Distance,
    HnswConfigDiff,
    ScalarQuantizationConfig,
    ScalarType,
    OptimizersConfigDiff,
    QuantizationSearchParams,
    SearchParams
)
from qdrant_client import QdrantClient
import openai
from openai.types import CreateEmbeddingResponse
from typing import Callable, List
import html
import os
import re

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")

# Initialize Qdrant initialized_qdrant_client
initialized_qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333")
)


def get_qdrant_client():
    return initialized_qdrant_client


def embed_text(text: str) -> List[float]:
    """Embeds a single piece of text using OpenAI's text-embedding-3-small."""
    try:
        response: CreateEmbeddingResponse = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"[ERROR] Embedding failed: {e}")
        return []


def create_collection_if_not_exists(collection_name, vector_size: int = 1536):
    """Create Qdrant collection if it doesn't exist"""
    qdrant_client = get_qdrant_client()
    if qdrant_client.collection_exists(collection_name):
        return

    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
            on_disk=True,  # Store full vectors on disk
        ),
        quantization_config=ScalarQuantization(
            scalar=ScalarQuantizationConfig(
                # Clamp extreme values to reduce error :contentReference[oaicite:2]{index=2}
                type=ScalarType.INT8,
                # Keep quantized vectors in RAM :contentReference[oaicite:3]{index=3}
                quantile=0.99,
                always_ram=True,
            )
        ),
        hnsw_config=HnswConfigDiff(
            m=32,  # Higher connectivity = improved precision
            ef_construct=200,  # Better index quality during build
        ),
        optimizers_config=OptimizersConfigDiff(
            default_segment_number=0,  # Let Qdrant auto-manage segment counts
            # Use memmap above this point count :contentReference[oaicite:4]{index=4}
            memmap_threshold=100_000,
        ),
    )


def chunked_upsert(client: QdrantClient, collection_name: str, points: list[PointStruct], chunk_size: int = 100):
    """
    Perform batched upsert to avoid timeout errors.
    """
    for i in range(0, len(points), chunk_size):
        chunk = points[i:i + chunk_size]
        client.upsert(
            collection_name=collection_name,
            points=chunk,
            wait=True
        )


async def upsert_to_qdrant(collection_name: str, items: list, search_text_transformator: Callable):
    """
    Upserts a list of items to a Qdrant collection.

    This function takes a list of items, transforms each item into searchable text using
    the provided `search_text_transformator` function, generates embeddings for the text,
    and then upserts these embeddings and the original item data into the specified Qdrant collection.

    Args:
        collection_name (str): The name of the Qdrant collection to upsert the items into.
        items (list): A list of items to upsert. Each item should be a dictionary or object
                              that can be serialized into JSON.
        search_text_transformator (Callable): A function that takes an item as input and returns
                                              a string of text that will be used to generate the embedding.
                                              This function is responsible for extracting the relevant
                                              information from the item and formatting it into a searchable text.
    """
    print(f"Upserting items to Qdrant collection: {collection_name}...")

    create_collection_if_not_exists(
        collection_name=collection_name)

    points = []

    for i, item in enumerate(items):

        print(f"Processing item {i + 1}/{len(items)}...")

        text = search_text_transformator(item)
        print(f"Text to embed: {text}")

        # Generate the embedding vector for the text.
        vector = embed_text(text)

        # Print the first 5 elements for brevity
        print(f"Vector embedding: {vector[:5]}...")

        # Create a PointStruct object for Qdrant, which includes the item ID, the embedding vector, and the original item data as payload.
        points.append(PointStruct(
            id=i, vector=vector, payload=item))

    # Upsert the PointStruct objects into the Qdrant collection.
    chunked_upsert(client=get_qdrant_client(),
                   collection_name=collection_name, points=points)
    print(
        f"Successfully upserted {len(points)} items to collection '{collection_name}'")


def clean_text(text):
    """
    Clean text by removing HTML tags while preserving text content.
    Also removes HTML comments and artifacts even if they appear within tag content.
    Uses only built-in Python libraries.

    Args:
        text (str): The raw text with HTML entities and tags

    Returns:
        str: Cleaned text with only the actual content preserved
    """
    # Step 1: Decode HTML entities (&lt; becomes <, &gt; becomes >, etc.)
    # html.unescape() handles all common HTML entities automatically
    decoded_text = html.unescape(text)

    # Step 2: Remove HTML/XML comments (<!-- ... -->) everywhere, including inside content
    text = re.sub(r'<!--.*?-->', '', decoded_text, flags=re.DOTALL)

    # Step 3: Remove CDATA sections (<![CDATA[ ... ]]>)
    text = re.sub(r'<!\[CDATA\[.*?\]\]>', '', text, flags=re.DOTALL)

    # Step 4: Remove XML declarations and processing instructions
    text = re.sub(r'<\?xml.*?\?>', '', text, flags=re.DOTALL)
    text = re.sub(r'<\!DOCTYPE.*?>', '', text, flags=re.DOTALL)

    # Step 5: Remove all HTML/XML tags but keep the content inside them
    # This removes <tag>, </tag>, and <tag/> but preserves the text content
    text = re.sub(r'<[^>]*>', '', text)

    # Step 6: Clean up extra whitespace and trim
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def search_with_precise_reranking(collection_name: str, query_vector: list[float], limit: int = 10):
    # Step 1: Retrieve an oversampled batch using quantized index
    oversample_factor = 2.0
    params = SearchParams(
        quantization=QuantizationSearchParams(
            ignore=False,
            rescore=True,
            oversampling=oversample_factor,
        ),
        hnsw_ef=128,                          # Higher ef for better search quality
    )

    results = get_qdrant_client().search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        search_params=params,
        with_payload=True,
    )
    return results
