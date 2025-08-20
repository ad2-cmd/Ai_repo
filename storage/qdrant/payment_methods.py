from shoprenter.payment_methods import get_enabled_payment_methods
from qdrant.util import clean_text, upsert_to_qdrant
import os


def payment_method_to_text(payment_method: dict) -> str:
    """
    Generates a comprehensive text representation of a payment_method from a payment_method dictionary.

    This function extracts various attributes of a payment_method, such as name, description, tags,
    price, brand, parameters, and attributes, and concatenates them into a single string.
    The resulting string provides a detailed overview of the payment_method, suitable for generating
    embeddings for semantic search.

    Args:
        payment_method (dict): A dictionary containing payment_method information.

    Returns:
        str: A string containing a detailed text representation of the payment_method.
    """

    # Extract payment_method descriptions, defaulting to an empty dictionary if missing.
    payment_method_descriptions = payment_method.get(
        'paymentDescription') or []

    # Initialize an empty string to store the Hungarian payment_method description.
    payment_method_description = {}

    # Iterate through the payment_method descriptions to find Hungarian tags.
    for description in payment_method_descriptions:
        # Check if the description has a country code and if it is 'hu' (Hungarian).
        if description.get('language', {}).get('code', '').lower() == 'hu':
            # If the description is Hungarian, extract the tags and break the loop.
            payment_method_description = description
            break

    # Extract the payment_method name from the descriptions, defaulting to an empty string if missing.
    name = clean_text(payment_method_description.get("name") or "")

    # Extract the payment_method short description from the descriptions and remove HTML tags.
    description = clean_text(
        payment_method_description.get("description") or "")

    # Construct the final text representation of the name of the payment method.
    final_name = ""
    if description:
        final_name = f"{name} fizetési mód részletes tudnivalói a következők: {description.lower().rstrip('.')}. "
    else:
        final_name = f"{name} fizetési mód"

    return (
        f"{final_name}"
    )


async def update_qdrant_payment_methods(payment_methods: list, languages: list):
    """
    Updates the Qdrant collection with the latest payment_method data from the Shoprenter API.

    This function retrieves the latest payment_method data, then calls `upsert_payment_methods_to_qdrant`
    to update the Qdrant collection with this data.
    """
    try:
        # Retrieve the latest payment_method data from the Shoprenter API.
        # payment_methods = await get_enabled_payment_methods(languages=languages)

        # Get the Qdrant collection name from the environment variables, default to 'payment-methods-test' if not set.
        collection_name = os.getenv(
            "QDRANT_COLLECTION_PAYMENT_METHODS", 'payment-methods-test')

        # Upsert the retrieved payment_methods into the Qdrant collection.
        await upsert_to_qdrant(collection_name=collection_name, items=payment_methods,
                               search_text_transformator=payment_method_to_text)
    except Exception as e:
        print('Failed to update qdrant payment methods')
        print(e)
