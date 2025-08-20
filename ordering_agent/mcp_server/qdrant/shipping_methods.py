
import os

from qdrant.util import embed_text, get_qdrant_client, search_with_precise_reranking


def get_all_shipping_methods():
    shipping_methods_raw = get_qdrant_client().scroll(
        collection_name=os.getenv(
            "QDRANT_COLLECTION_SHIPPING_METHODS", 'shipping-methods-test'),
        limit=20,
        with_payload=True,
        with_vectors=False,
    )

    return [method.payload for method in shipping_methods_raw[0]]


def search_qdrant_shipping_methods(query: str, limit: int = 10):
    query_vector = embed_text(query)

    # Get the Qdrant collection name from the environment variables, default to 'shipping-methods-test' if not set.
    collection_name = os.getenv(
        "QDRANT_COLLECTION_SHIPPING_METHODS", 'shipping-methods-test')

    # Search the Qdrant collection for points that are similar to the query vector.
    search_result = search_with_precise_reranking(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit
    )

    return search_result
