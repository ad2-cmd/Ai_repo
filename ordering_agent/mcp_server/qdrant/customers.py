import os
from typing import Dict, List
from qdrant.util import embed_text, get_qdrant_client, search_with_precise_reranking
from qdrant_client import models


def search_customers(query: str, limit: int = 10):
    """
    Searches for customers in the Qdrant collection that are semantically similar to the given query.

    This function takes a query string, generates an embedding for it, and then searches the Qdrant
    collection for customers with embeddings that are close to the query embedding.

    Args:
        query (str): The query string to search for similar customers.
        limit (int): The maximum number of search results to return. Defaults to 10.

    Returns:
        list: A list of search results, where each result is a dictionary containing customer information.
    """
    # Generate the embedding vector for the query string.
    query_vector = embed_text(query)

    # Get the Qdrant collection name from the environment variables, default to 'customers-test' if not set.
    collection_name = os.getenv(
        "QDRANT_COLLECTION_CUSTOMERS", 'customers-test')

    # Search the Qdrant collection for points that are similar to the query vector.
    search_result = search_with_precise_reranking(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit
    )

    return search_result


def search_qdrant_customers(query: str):
    """
    Searches for customers in the Qdrant collection that are semantically similar to the given query.

    This function takes a query string, calls `search_customers` to find similar customers in Qdrant,
    and then returns the points (customer data) from the search results.

    Args:
        query (str): The query string to search for similar customers.

    Returns:
        list: A list of customer data dictionaries that are similar to the query.
    """
    # Search for customers in the Qdrant collection that are similar to the query.
    results = search_customers(query)

    # Extract the points (customer data) from the search results and return them.
    return results


def search_qdrant_customers_directly(filters: Dict[str, str]):
    # Get the Qdrant collection name from the environment variables, default to 'customers-test' if not set.
    collection_name = os.getenv(
        "QDRANT_COLLECTION_CUSTOMERS", 'customers-test')

    client = get_qdrant_client()

    must: List[models.Condition] = [models.FieldCondition(key=key, match=models.MatchValue(
        value=value)) for key, value in filters.items()]

    results = client.scroll(
        collection_name=collection_name,
        scroll_filter=models.Filter(
            must=must
        ),
    )

    return results[0]
