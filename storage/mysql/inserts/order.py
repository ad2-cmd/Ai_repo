
import json
from mysql.util import upsert_record
from shoprenter.shoprenter import get_all_shoprenter_items, resolve_linked_resource
from mysql.db import db
from mysql.models.order import Order


async def get_orders_from_shoprenter():

    products = await get_all_shoprenter_items(
        endpoint='productExtend')

    orders = await get_all_shoprenter_items('/orderExtend')

    for order in orders:
        orderedProducts = order.get('orderProducts', [])
        for product in orderedProducts:
            product = await resolve_linked_resource(
                product, 'product', products)

        order['orderProducts'] = orderedProducts

    return orders


async def update_orders_in_db():
    orders = await get_orders_from_shoprenter()

    session = db.get_session()

    for order in orders:
        upsert_record(session, Order, order)

    session.commit()
    session.close()
