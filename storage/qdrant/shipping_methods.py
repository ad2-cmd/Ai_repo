from shoprenter.shipping_methods import get_enabled_shipping_methods
from qdrant.util import clean_text, upsert_to_qdrant
import os


def shipping_method_to_text(shipping_method: dict) -> str:
    """
    Generates a comprehensive text representation of a shipping_method from a shipping_method dictionary.

    This function extracts various attributes of a shipping_method, such as name, description, tags,
    price, brand, parameters, and attributes, and concatenates them into a single string.
    The resulting string provides a detailed overview of the shipping_method, suitable for generating
    embeddings for semantic search.

    Args:
        shipping_method (dict): A dictionary containing shipping_method information.

    Returns:
        str: A string containing a detailed text representation of the shipping_method.
    """

    # Extract shipping_method descriptions, defaulting to an empty dictionary if missing.
    shipping_method_descriptions = shipping_method.get(
        'shippingModeDescriptions') or []

    # Extract shipping_method prices, defaulting to an empty list containing an empty dictionary if missing,
    # then take the first price entry.
    shipping_method_lanes = (shipping_method.get(
        'shippingLanes') or [{}])

    # Initialize an empty string to store the tags.
    lanes = ""

    # Iterate through the shipping_method tags to find Hungarian tags.
    for i, lane in enumerate(shipping_method_lanes):
        lanes += f"{i + 1}. Szállítási tartomány:\n"
        lanes += f"    Kosár összeg minimum: {lane.get('cartMinimumGross') or 'N/A'}\n"
        lanes += f"    Kosár összeg maximum: {lane.get('cartMaximumGross') or 'N/A'}\n"
        lanes += f"    Nettó szállítási költség: {lane.get('costNet') or 'N/A'}\n"
        lanes += f"    Minimum csomag súly: {lane.get('weightMinimum') or 'N/A'}\n"
        lanes += f"    Maximum csomag súly: {lane.get('weightMaximum') or 'N/A'}\n"

    # Initialize an empty string to store the Hungarian shipping_method description.
    shipping_method_description = {}

    # Iterate through the shipping_method descriptions to find Hungarian tags.
    for description in shipping_method_descriptions:
        # Check if the description has a country code and if it is 'hu' (Hungarian).
        if description.get('language', {}).get('code', '').lower() == 'hu':
            # If the description is Hungarian, extract the tags and break the loop.
            shipping_method_description = description
            break

    # Extract the shipping_method name from the descriptions, defaulting to an empty string if missing.
    name = clean_text(shipping_method_description.get("name") or "")

    # Extract the shipping_method short description from the descriptions and remove HTML tags.
    description = clean_text(
        shipping_method_description.get("description") or "")

    shipping_lanes_final = ""
    if len(shipping_method_lanes) > 0:
        shipping_lanes_final = f"Szállítási tartományok:\n {lanes}"

    # Construct the final text representation of the shipping_method.
    return (
        f"{name} szállítási mód részletes tudnivalói a következők: {description.lower().rstrip('.')}. "
        f"{shipping_lanes_final}"
    )


async def update_qdrant_shipping_methods(shipping_methods: list, languages: list):
    """
    Updates the Qdrant collection with the latest shipping_method data from the Shoprenter API.

    This function retrieves the latest shipping_method data, then calls `upsert_shipping_methods_to_qdrant`
    to update the Qdrant collection with this data.
    """
    try:
        # Retrieve the latest shipping_method data from the Shoprenter API.
        # shipping_methods = await get_enabled_shipping_methods(languages=languages)

        # Get the Qdrant collection name from the environment variables, default to 'shipping-methods-test' if not set.
        collection_name = os.getenv(
            "QDRANT_COLLECTION_SHIPPING_METHODS", 'shipping-methods-test')

        # Upsert the retrieved shipping_methods into the Qdrant collection.
        await upsert_to_qdrant(collection_name=collection_name, items=shipping_methods,
                               search_text_transformator=shipping_method_to_text)

    except Exception as e:
        print('Failed to update qdrant shipping methods')
        print(e)
