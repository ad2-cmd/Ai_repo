from qdrant.util import clean_text, upsert_to_qdrant
from shoprenter.products import get_products
import os


def product_to_text(product: dict) -> str:
    """
    Generates a comprehensive text representation of a product from a product dictionary.

    This function extracts various attributes of a product, such as name, description, tags,
    price, brand, parameters, and attributes, and concatenates them into a single string.
    The resulting string provides a detailed overview of the product, suitable for generating
    embeddings for semantic search.

    Args:
        product (dict): A dictionary containing product information.

    Returns:
        str: A string containing a detailed text representation of the product.
    """

    # Extract product descriptions, defaulting to an empty dictionary if missing.
    product_descriptions = product.get('productDescriptions') or []

    # Extract product tags, defaulting to an empty list containing an empty dictionary if missing.
    product_tags = product.get('productTags') or []

    # Extract product prices, defaulting to an empty list containing an empty dictionary if missing,
    # then take the first price entry.
    product_prices = (product.get('productPrices') or [{}])[0]

    # Extract product manufacturer information, defaulting to an empty dictionary if missing.
    product_manufacturer = product.get('manufacturer') or {}

    # Initialize an empty string to store the tags.
    tags = ""

    # Iterate through the product tags to find Hungarian tags.
    for tag in product_tags:
        # Check if the tag has a country code and if it is 'hu' (Hungarian).
        if tag.get('language', {}).get('code', '').lower() == 'hu':
            # If the tag is Hungarian, extract the tags and break the loop.
            tags = tag.get('tags')
            break

    # Initialize an empty string to store the Hungarian product description.
    product_description = {}

    # Iterate through the product descriptions to find Hungarian tags.
    for description in product_descriptions:
        # Check if the description has a country code and if it is 'hu' (Hungarian).
        if description.get('language', {}).get('code', '').lower() == 'hu':
            # If the description is Hungarian, extract the tags and break the loop.
            product_description = description
            break

    # Extract the product name from the descriptions, defaulting to an empty string if missing.
    name = clean_text(product_description.get("name") or "")

    # Extract the product short description from the descriptions and remove HTML tags.
    short_description = clean_text(
        product_description.get("shortDescription") or "")

    description = clean_text(
        product_description.get("description") or "")

    # Extract the product price from the prices, defaulting to None if missing.
    price = product_prices.get("gross") or None

    # Extract the product brand from the manufacturer information, defaulting to None if missing.
    brand = product_manufacturer.get("name") or None

    # Extract the product parameters, defaulting to an empty string if missing.
    parameters = product.get("parameters") or None

    custom_content_title = product.get("customContentTitle") or None
    custom_content = product.get("customContent") or None

    product_tags_final = ""
    if (len(product_tags) > 0):
        product_tags_final = f"A termék címkéi: {tags}. "

    price_final = ""
    if (price):
        price_final = f"A termék ára: {price} forint. "

    brand_final = ""
    if brand:
        brand_final = f"A termék {brand} márkájú. "

    custom_content_final = ""
    if custom_content_title and custom_content:
        custom_content_final = f"{custom_content_title}: {custom_content}. "

    parameters_final = ""
    if parameters:
        parameters_final = f"{parameters}."

    # Construct the final text representation of the product.
    return (
        f"A(z) {name} egy {description.lower().rstrip('.')}. "
        f"Röviden {short_description} "
        f"{product_tags_final} "
        f"{price_final} "
        f"{brand_final} "
        f"{parameters_final} "
        f"{custom_content_final} "
    )


async def update_qdrant_products(products: list, languages: list):
    """
    Updates the Qdrant collection with the latest product data from the Shoprenter API.

    This function retrieves the latest product data, then calls `upsert_products_to_qdrant`
    to update the Qdrant collection with this data.
    """
    try:
        # Retrieve the latest product data from the Shoprenter API.
        # products = await get_products(languages=languages)

        # Get the Qdrant collection name from the environment variables, default to 'products-test' if not set.
        collection_name = os.getenv(
            "QDRANT_COLLECTION_PRODUCTS", 'products-test')

        # Upsert the retrieved products into the Qdrant collection.
        await upsert_to_qdrant(collection_name=collection_name,
                               items=products, search_text_transformator=product_to_text)
    except Exception as e:
        print('Failed to update qdrant products')
        print(e)
