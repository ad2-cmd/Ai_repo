from qdrant.util import clean_text
from shoprenter.shoprenter import find_resource_by_id, get_all_shoprenter_items, resolve_linked_resource
import json


async def get_shipping_methods(languages: list):
    shipping_methods = await get_all_shoprenter_items('shippingModeExtend')
    tax_classes = await get_all_shoprenter_items('taxClasses')
    tax_rates = await get_all_shoprenter_items('taxRates')

    for tax_class in tax_classes:
        tax_class_tax_rates = []
        for tax_rate in tax_rates:
            tax_rate_tax_class_id = tax_rate.get(
                'taxClass', {}).get('href', '').split('/')[-1]
            if tax_rate_tax_class_id != tax_class.get('id'):
                continue

            tax_class_tax_rates.append(tax_rate)

        tax_class_tax_rates.sort(key=lambda x: x['priority'])
        tax_class['taxRates'] = tax_class_tax_rates

    for shipping_method in shipping_methods:
        if (len(shipping_method.get('shippingModeDescriptions')) > 0):
            shipping_method_descriptions = shipping_method.get(
                'shippingModeDescriptions')
            for shipping_method_description in shipping_method_descriptions:
                shipping_method_description = await resolve_linked_resource(
                    shipping_method_description, 'language', languages)
                shipping_method_description['name'] = clean_text(
                    shipping_method_description['name'])
                shipping_method_description['description'] = clean_text(
                    shipping_method_description['description'])

            shipping_method['shippingModeDescriptions'] = shipping_method_descriptions

        if shipping_method.get('taxClass', None):
            shipping_method = await resolve_linked_resource(
                shipping_method, 'taxClass', tax_classes)

    return shipping_methods


async def get_enabled_shipping_methods(languages: list):
    shipping_methods = await get_shipping_methods(languages=languages)
    enabled_shipping_methods = []
    for shipping_method in shipping_methods:
        if shipping_method.get('enabled') != '1' and shipping_method.get('enabled') != 1:
            continue
        enabled_shipping_methods.append(shipping_method)

    return shipping_methods
