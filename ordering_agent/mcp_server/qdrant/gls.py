
import os
from qdrant.util import embed_text, search_with_precise_reranking


def search_qdrant_gls_parcel_machines(query: str, limit: int = 10):
    query_vector = embed_text(query)

    # Get the Qdrant collection name from the environment variables, default to 'gls-parcel-machines' if not set.
    collection_name = os.getenv(
        "QDRANT_COLLECTION_GLS", 'gls-parcel-machines')

    # Search the Qdrant collection for points that are similar to the query vector.
    search_result = search_with_precise_reranking(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit
    )

    return search_result
