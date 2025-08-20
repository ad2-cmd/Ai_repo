from qdrant.util import clean_text
from shoprenter.shoprenter import get_all_shoprenter_items, resolve_linked_resource


async def get_payment_methods(languages: list):
    payment_methods = await get_all_shoprenter_items('paymentModes')

    for payment_method in payment_methods:
        if (len(payment_method.get('paymentDescription')) > 0):
            payment_method_descriptions = payment_method.get(
                'paymentDescription')
            for payment_method_description in payment_method_descriptions:
                payment_method_description = await resolve_linked_resource(
                    payment_method_description, 'language', languages)
                payment_method_description['name'] = clean_text(
                    payment_method_description['name'])
                payment_method_description['description'] = clean_text(
                    payment_method_description['description'])

            payment_method['paymentDescription'] = payment_method_descriptions

    return payment_methods


async def get_enabled_payment_methods(languages: list):
    payment_methods = await get_payment_methods(languages=languages)
    enabled_payment_methods = []
    for payment_method in payment_methods:
        if payment_method.get('status') != '1' and payment_method.get('status') != 1:
            continue

        enabled_payment_methods.append(payment_method)

    return enabled_payment_methods
