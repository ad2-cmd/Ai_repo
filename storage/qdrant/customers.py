from qdrant.util import upsert_to_qdrant
from shoprenter.customers import get_customers
import os


def customer_to_text(customer: dict) -> str:
    first = customer.get('firstname', '')
    last = customer.get('lastname', '')
    email = customer.get('email', '')
    phone = customer.get('telephone', '')

    shipping = customer.get('defaultAddress') or None
    city = ''
    address = ''
    country = ''
    if (shipping is not None and shipping != {}):
        city = shipping.get('city', '')
        address = shipping.get('address1', '')
        country = shipping.get('country', {}).get('name', '')

    # total_spent = customer.get('totalSpent', 0)
    # orders_count = customer.get('ordersCount', 0)
    # last_order = customer.get('lastOrderDate', 'ismeretlen dátum')

    customer_introduction = f"A vásárló neve {first} {last}."
    customer_shipping_address = ""
    if (shipping is not None):
        customer_introduction = f"{first} {last} nevű vásárló {city} városból, {country} területéről."
        customer_shipping_address = f"Szállítási cím: {address}, {city}. "

    return (
        f"{customer_introduction} "
        # f"{orders_count} rendelést adott le, összesen {total_spent} forint értékben. "
        # f"Legutóbbi rendelése {last_order} dátumon történt. "
        f"{customer_shipping_address}"
        f"Elérhetősége: {email}, {phone}. "
    )


async def update_qdrant_customers(customers: list, countries: list, addresses: list):
    """
    Updates the Qdrant collection with the latest customer data from the Shoprenter API.

    This function retrieves the latest customer data, then calls `upsert_customers_to_qdrant`
    to update the Qdrant collection with this data.
    """
    try:
        # Retrieve the latest customer data from the Shoprenter API.
        # customers = await get_customers(countries=countries, addresses=addresses)

        # Get the Qdrant collection name from the environment variables, default to 'customers-test' if not set.
        collection_name = os.getenv(
            "QDRANT_COLLECTION_CUSTOMERS", 'customers-test')

        # Upsert the retrieved customers into the Qdrant collection.
        await upsert_to_qdrant(collection_name=collection_name,
                               items=customers, search_text_transformator=customer_to_text)
    except Exception as e:
        print('Failed to update qdrant customers')
        print(e)
