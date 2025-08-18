from dotenv import load_dotenv
from qdrant_client.models import (
    QuantizationSearchParams,
    SearchParams
)
from qdrant_client import QdrantClient
import openai
from openai.types import CreateEmbeddingResponse
from typing import List
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
