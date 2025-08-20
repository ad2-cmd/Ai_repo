from typing import Annotated
from fastmcp import Context
from pydantic import BaseModel, Field

from mcp_utils.products import search_product, search_products
from mcp_utils.session import SessionManager


class ProductId(BaseModel):
    id: Annotated[str, Field(description="The id of the product")]
    quantity: Annotated[int, Field(description="The number of the product")]


class ProductTools:
    @classmethod
    async def search_for_products(cls, ctx: Context, query: str):
        """
        Search for product(s) by a query description.

        This tool searches for products based on a given query string.
        It uses the query to find relevant products in the database and returns a list of product details.
        """

        products = await search_products(query)

        session_manager = SessionManager().get_session(ctx.session_id)
        # session_manager.found_products.extend(products)

        for product in products:
            product_id = product.get('id', '')

            # Look for the product in the found_products list
            for i, found_product in enumerate(session_manager.found_products):
                if found_product.get('id', '') == product_id:
                    # Update existing product and stop checking further
                    session_manager.found_products[i] = product
                    break
            else:
                # This else runs only if no break happened — means it's new
                session_manager.found_products.append(product)

        return session_manager.found_products

    @classmethod
    async def search_for_product(cls, ctx: Context, query: str):
        """
        Search for a single product by a query description.

        This tool searches for a specific product based on a given query string.
        It is intended to return a single, most relevant product that matches the query.
        """

        product = await search_product(query)

        session_manager = SessionManager().get_session(ctx.session_id)
        session_manager.found_products.append(product)

        return product

    @classmethod
    async def add_selected_products_to_cart(cls, ctx: Context, product_ids: list[ProductId]):
        """
        Adds products to the cart based on their IDs.

        This tool takes a list of product IDs and adds the corresponding products to the user's cart.
        It retrieves the product details from the database using the IDs and updates the cart accordingly.
        """

        session_manager = SessionManager().get_session(ctx.session_id)
        products = session_manager.found_products

        selected_products = []

        for product_id in product_ids:
            for product in products:
                if product.get('id', '') != product_id.id:
                    continue

                product['quantity'] = product_id.quantity

                selected_products.append(product)

        # selected_products = [
        #     product for product in products if product.get('id', '') in product_ids
        # ]

        if not selected_products:
            return {
                "status": "unsuccessfull",
                "product_ids": product_ids
            }

        # session_manager.products.extend(selected_products)

        for selected_product in selected_products:
            product_id = selected_product.get('id', '')

            # Look for the product in the found_products list
            for i, found_product in enumerate(session_manager.products):
                if found_product.get('id', '') == product_id:
                    # Update existing product and stop checking further
                    session_manager.products[i] = selected_product
                    break
            else:
                # This else runs only if no break happened — means it's new
                session_manager.products.append(selected_product)

        return {
            "status": "successfull",
            "product_ids": [product.get('id', '') for product in session_manager.products]
        }
