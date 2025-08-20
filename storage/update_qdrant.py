import asyncio
from qdrant.customers import update_qdrant_customers
from qdrant.foxpost import update_foxpost_parcel_machines
from qdrant.gls import update_gls_parcel_machines
from qdrant.payment_methods import update_qdrant_payment_methods
from qdrant.products import update_qdrant_products
from qdrant.shipping_methods import update_qdrant_shipping_methods
from shoprenter.customers import get_customers
from shoprenter.payment_methods import get_enabled_payment_methods
from shoprenter.products import get_enabled_products
from shoprenter.shipping_methods import get_enabled_shipping_methods
from shoprenter.shoprenter import get_all_shoprenter_items
from time import sleep


async def update_qdrant():
    try:
        languages = await get_all_shoprenter_items(endpoint='languages')
        countries = await get_all_shoprenter_items(endpoint='countries')
        addresses = await get_all_shoprenter_items(endpoint='addresses')

        products = await get_enabled_products(languages=languages)
        customers = await get_customers(countries=countries, addresses=addresses)
        shipping_methods = await get_enabled_shipping_methods(languages=languages)
        payment_methods = await get_enabled_payment_methods(languages=languages)

        await asyncio.gather(
            update_qdrant_products(products=products, languages=languages),
            update_qdrant_customers(customers=customers,
                                    countries=countries, addresses=addresses),
            update_qdrant_shipping_methods(
                shipping_methods=shipping_methods, languages=languages),
            update_qdrant_payment_methods(
                payment_methods=payment_methods, languages=languages),
            update_gls_parcel_machines(),
            update_foxpost_parcel_machines(),
        )
    except Exception as e:
        print('Waiting for 10 seconds')
        sleep(10)
        await update_qdrant()
        print(e)
