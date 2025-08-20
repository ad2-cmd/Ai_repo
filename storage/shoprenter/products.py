from qdrant.util import clean_text
from shoprenter.shoprenter import call_shoprenter_api, get_all_shoprenter_items, resolve_linked_resource


async def get_products(languages: list, filters=None):
    """Get products with optional filters"""
    products = await get_all_shoprenter_items(
        endpoint='productExtend', filters=filters)

    for product in products:
        if (len(product.get('productTags')) > 0):
            product_tags = product.get('productTags')
            for product_tag in product_tags:
                product_tag = await resolve_linked_resource(
                    product_tag, 'language', languages)

            product['productTags'] = product_tags

        if (len(product.get('productDescriptions')) > 0):
            product_descriptions = product.get('productDescriptions')
            for product_description in product_descriptions:
                product_description = await resolve_linked_resource(
                    product_description, 'language', languages)
                product_description['name'] = clean_text(
                    product_description['name'])
                product_description['description'] = clean_text(
                    product_description['description'])
                product_description['shortDescription'] = clean_text(
                    product_description['shortDescription'])

            product['productDescriptions'] = product_descriptions

    return products


async def get_product(product_id):
    """Get a specific product"""
    return await call_shoprenter_api('GET', f'productExtend/{product_id}')


async def get_enabled_products(languages: list):
    products = await get_products(languages=languages)
    enabled_products = []
    for product in products:
        if product.get('status') != '1' and product.get('status') != 1:
            continue

        enabled_products.append(product)

    return enabled_products
