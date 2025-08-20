from shoprenter.shoprenter import call_shoprenter_api, get_all_shoprenter_items, resolve_linked_resource


async def get_orders(countries: list, addresses: list, filters=None):
    """Get customers with optional filters"""
    customers = await get_all_shoprenter_items(
        endpoint='customerExtend', filters=filters)

    for customer in customers:
        if (customer.get('defaultAddress')):
            customer = await resolve_linked_resource(
                customer, 'defaultAddress', all_resources=addresses)
            customer['defaultAddress'] = await resolve_linked_resource(
                customer['defaultAddress'], 'country', countries)

        customer_addresses = customer.get('addresses')
        if customer_addresses:
            for i in range(len(customer_addresses)):
                customer['addresses'][i] = await resolve_linked_resource(
                    customer_addresses[i], 'country', countries)

    return customers


async def get_order(customer_id):
    """Get a specific customer"""
    return await call_shoprenter_api('GET', f'orderExtend/{customer_id}')
