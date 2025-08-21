from typing import Annotated, Any
from pydantic import BaseModel, Field
from qdrant.products import search_qdrant_products
from qdrant_client.models import ScoredPoint


async def search_product(query: str):
    products = search_qdrant_products(query)
    return get_product_details(products[0])


async def search_products(query: str):
    products_raw = search_qdrant_products(query)
    products: list[dict[str, Any]] = []

    for product_raw in products_raw:
        products.append(get_product_details(product_raw))

    return products


def get_product_details(product_raw: ScoredPoint) -> dict[str, Any]:

    product = product_raw.payload

    if not product:
        return {
        'id': None,
        'sku': None,
        'model_number': None,
        'name': None,
        'brand': None,
        'price': None,
        'price_net': None,
        'original_price': None,
        'original_price_net': None,
        'short_description': None,
        'width': None,
        'height': None,
        'length': None,
        'weight': None,
        # 'description': None,
    }

    product_id = product.get('id')
    product_sku = product.get('sku')
    product_model_number = product.get('modelNumber') or None
    product_price_raw = product.get('productPrices', [])

    product_price = None
    product_price_net = None
    product_original_price = None
    product_original_price_net = None
    if len(product_price_raw) > 0:
        product_price = product_price_raw[0].get('gross', '0')
        product_price_net = product_price_raw[0].get('net', '')
        product_original_price = product_price_raw[0].get('grossOriginal', '0')
        product_original_price_net = product_price_raw[0].get('netOriginal', '')

    product_brand = None
    product_brand_raw = product.get('manufacturer', {})
    if type(product_brand_raw) == list:
        if len(product_brand_raw) > 0:
            product_brand = product_brand_raw[0].get('name')
    else:
        product_brand = product_brand_raw.get('name')

    product_descriptions_raw = product.get('productDescriptions', [])
    product_descriptions = product_descriptions_raw[0]

    for product_description_raw in product_descriptions_raw:
        if product_description_raw.get('language', {}).get('code') == 'hu':
            product_descriptions = product_description_raw
            break

    product_name = product_descriptions.get('name', '')
    product_description = product_descriptions.get('description', '')[:200]
    product_short_description = product_descriptions.get(
        'shortDescription', '')

    product_width = product.get('width', '0.00')
    product_height = product.get('height', '0.00')
    product_length = product.get('length', '0.00')
    product_weight = product.get('weight', '0.00')

    return {
        'id': product_id,
        'sku': product_sku,
        'model_number': product_model_number,
        'name': product_name,
        'brand': product_brand,
        'price': product_price,
        'price_net': product_price_net,
        'original_price': product_original_price,
        'original_price_net': product_original_price_net,
        'short_description': product_short_description,
        'width': product_width,
        'height': product_height,
        'length': product_length,
        'weight': product_weight
        # 'description': product_description,
    }


class Product(BaseModel):
    id: Annotated[str, Field(description="The id of the product")]
    sku: Annotated[str, Field(description="The sku of the product")]
    name: Annotated[str, Field(description="The name of the product")]
    brand: Annotated[str, Field(description="The brand of the product")]
    price: Annotated[str, Field(description="The price of the product")]
    short_description: Annotated[str, Field(
        description="The short_description of the product")]
    description: Annotated[str, Field(
        description="The description of the product")]

    def to_json(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "brand": self.brand,
            "price": self.price,
            "short_description": self.short_description,
            "description": self.description,
        }
