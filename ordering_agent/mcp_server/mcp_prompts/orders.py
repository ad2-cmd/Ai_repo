

import json
from fastmcp import Context
from fastmcp.prompts.prompt import Message
from mcp.types import PromptMessage, TextContent
from datetime import datetime
import time
import random

from mcp_utils.session import Session, SessionManager
from shoprenter.shoprenter import call_shoprenter_api


class OrderPrompts:
    @classmethod
    async def order_confirmation(cls, ctx: Context):
        """Show order summary"""

        session_manager = SessionManager().get_session(ctx.session_id)
        customer_raw = session_manager.customer
        products_raw = session_manager.products
        shipping_address_raw = session_manager.shipping_address
        payment_method_raw = session_manager.payment_method
        shipping_method_raw = session_manager.shipping_method

        customer = {
            "name": customer_raw.get('name', ''),
            "email": customer_raw.get('email', ''),
            "telephone": customer_raw.get('telephone')
        }
        products = [{'sku': product.get('sku', ''), 'name': product.get('name', ''), 'brand': product.get(
            'brand', ''), 'price': product.get('price', '')} for product in products_raw]
        shipping_address = {
            "lastname": shipping_address_raw.get('lastname', ''),
            "firstname": shipping_address_raw.get('firstname', ''),
            "postcode": shipping_address_raw.get('postcode', ''),
            "city": shipping_address_raw.get('city', ''),
            "address": shipping_address_raw.get('address', ''),
            "telephone": shipping_address_raw.get('telephone', ''),
        }
        payment_method = {
            "name": payment_method_raw.get('name', ''),
            "description": payment_method_raw.get('description', '')
        }
        shipping_method = {
            "name": shipping_method_raw.get('name', ''),
            "description": shipping_method_raw.get('description', '')
        }

        response = f"""
        ## Task
        Extract and return all information needed for an order summary from the input JSONs.
        Create an engaging order summary from the extracted information and help the user/customer to see what is in his/her order.
        Make sure to mask the sensitive shipping address values

        ## Inputs
        Customer: {json.dumps(customer, indent=4)}
        Products: {json.dumps(products, indent=4)}
        Shipping address: {json.dumps(shipping_address, indent=4)}
        Payment method: {json.dumps(payment_method, indent=4)}
        Shipping method: {json.dumps(shipping_method, indent=4)}

        ## Output
        An engaging and helpful order summary for the user to check everything is all set and good before proceeding to the order finalization
        """

        return Message(response, role="user")

    @classmethod
    async def order_finalization(cls, ctx: Context):
        """Finalize the order"""

        session_manager = SessionManager().get_session(ctx.session_id)
        customer = session_manager.customer
        shipping_address = session_manager.shipping_address
        shipping_method = session_manager.shipping_method
        payment_address = session_manager.payment_address
        payment_method = session_manager.payment_method

        # NOTE: Step 1: Create an Order Resource
        order_resource = prepare_order_resource(
            customer=customer,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            payment_address=payment_address,
            payment_method=payment_method
        )
        order = await create_order_resource(order_resource)
        print(order)

        order_id = order.get('id', '')

        # NOTE: Step 2: Add more items to Order Total
        order_totals = summarize_order_totals(
            session_manager=session_manager, order_id=order_id)

        await call_shoprenter_api(
            method='POST', endpoint=f'orderTotals', data=order_totals
        )

        # NOTE: Step 3: Add products to Order Product
        products = session_manager.products
        total_sum = 0  # for step 4
        for product in products:
            product_original_net = float(product.get('original_price_net', 0))
            product_net = float(product.get('price_net', 0))
            product_quantity = float(product.get('quantity', 0))
            product_total = product_net * product_quantity

            order_product = {
                "name": product.get('name', ''),
                "sku": product.get('sku', ''),
                "modelNumber": product.get('model_number', ''),
                "originalPrice": format_currency_number(product_original_net),
                "price": format_currency_number(product_net),
                "total": format_currency_number(product_total),
                "taxRate": "27.0000",
                "stock1": product_quantity,
                "stock2": "0",
                "subtractStock": product_quantity,
                "width": f"{float(product.get('width', 0)):.1f}",
                "height": f"{float(product.get('height', 0)):.1f}",
                "length": f"{float(product.get('length', 0)):.1f}",
                "weight": f"{float(product.get('weight', 0)):.2f}",
                "order": {
                    "id": order_id,
                },
                "product": {
                    "id": product.get('id', ''),
                },
            }

            await call_shoprenter_api(
                method='POST', endpoint='orderProducts', data=order_product
            )

            total_sum += product_total

        # NOTE: Step 4: Change the total value of the created Order Resource
        total_sum_string = f"{total_sum:.4f}"
        await call_shoprenter_api(
            method='PUT', endpoint=f'orders/{order_id}', data=total_sum_string
        )

        return PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"""
        ✅ RENDELÉS LEADVA!

        A rendelésedet sikeresen rögzítettük.

        🛒 Rendelésszám: #{order_resource.get('invoiceId', order.get('innerId', order_id))}
        💰 Végösszeg: {format_currency_number(total_sum)} Ft

        A rendelés részleteit és a számlát emailben elküldtük.
        Köszönjük a vásárlást, {customer.get('lastname', '')}!
        """))


def format_currency(amount, currency="Ft"):
    return f"{amount:,.0f} {currency}".replace(",", ".")


def format_currency_number(amount):
    return f"{amount:.4f}"


def summarize_order_totals(session_manager: Session, order_id=None):
    total = 0.0
    total_net = 0.0
    total_weight = 0.0
    shipping_cost_net = 0.0
    tax = 27.0

    order_totals = []

    payment_method = session_manager.payment_method

    products = session_manager.products
    for product in products:
        total += float(product.get('price', '0'))
        total_net += float(product.get('price_net', '0'))
        total_weight += float(product.get('weight', '0'))

    shipping_method = session_manager.shipping_method
    shipping_lanes = shipping_method.get('shippingLanes', [])
    for shipping_lane in shipping_lanes:
        weight_min = float(shipping_lane.get('weightMinimum', '0'))
        weight_max = float(shipping_lane.get('weightMaximum', '0'))

        if weight_min >= total_weight and weight_max <= total_weight:
            shipping_cost_net = float(shipping_lane.get('costNet', '0'))
            break

    shipping_tax_class = shipping_method.get('taxClass', {})
    shipping_tax_rate_dict = shipping_tax_class.get('taxRates', [{}])[0]
    shipping_tax_rate = float(shipping_tax_rate_dict.get('rate', '0'))

    shipping_cost_gross = shipping_cost_net * (1 + shipping_tax_rate / 100)

    net_partial_amount = {
        "name": "Nettó részösszeg:",
        "valueText": format_currency(total_net),
    }

    tax_cost_value = total - total_net
    tax_cost = {
        "name": "ÁFA (27%):",
        "valueText": format_currency(tax_cost_value),
    }

    gross_partial_amount = {
        "name": "Bruttó részösszeg:",
        "valueText": format_currency(total),
    }

    gross_shipping_cost = {
        "name": payment_method.get('name', ''),
        "valueText": format_currency(shipping_cost_gross)
    }

    cash_on_delivery_cost = None
    payment_method_payment_duty = payment_method.get('paymentDuty', {})
    cash_on_delivery_cost_value_net = float(
        payment_method_payment_duty.get('dutyFix', '0'))
    cash_on_delivery_cost_value_gross = cash_on_delivery_cost_value_net * \
        (1 + tax / 100)
    if payment_method.get('code', '') == 'cod':
        cash_on_delivery_cost = {
            "name": "Utánvétel:",
            "valueText": format_currency(cash_on_delivery_cost_value_gross),
        }

    cash_on_delivery_cost_value = cash_on_delivery_cost_value_gross if cash_on_delivery_cost else 0
    total_gross = total + shipping_cost_gross + cash_on_delivery_cost_value

    gross_total = {
        "name": "Összesen bruttó:",
        "valueText": format_currency(total_gross)
    }

    if order_id:
        net_partial_amount |= {
            "value": format_currency_number(total_net),
            "sortOrder": "3",
            "type": "SUB_TOTAL",
            "key": None,
            "description": None,
            "order": {
                "id": order_id
            }
        }
        tax_cost |= {
            "value": format_currency_number(tax_cost_value),
            "sortOrder": "3",
            "type": "TAX",
            "key": None,
            "description": None,
            "order": {
                "id": order_id
            }
        }
        gross_partial_amount |= {
            "value": format_currency_number(total),
            "sortOrder": "4",
            "type": "SUB_TOTAL_WITH_TAX",
            "key": None,
            "description": None,
            "order": {
                "id": order_id
            }
        }
        gross_shipping_cost |= {
            "value": format_currency_number(shipping_cost_gross),
            "sortOrder": "6",
            "type": "SHIPPING",
            "key": None,
            "description": None,
            "order": {
                "id": order_id
            }
        }
        gross_total |= {
            "value": format_currency_number(shipping_cost_gross),
            "sortOrder": "10",
            "type": "TOTAL",
            "key": None,
            "description": None,
            "order": {
                "id": order_id
            }
        }

    order_totals.append(net_partial_amount)
    order_totals.append(tax_cost)
    order_totals.append(gross_partial_amount)
    order_totals.append(gross_shipping_cost)

    if order_id and cash_on_delivery_cost:
        cash_on_delivery_cost |= {
            "value": format_currency_number(cash_on_delivery_cost_value_gross),
            "sortOrder": "8",
            "type": "PAYMENT",
            "key": None,
            "description": None,
            "order": {
                "id": order_id
            }
        }

        order_totals.append(cash_on_delivery_cost)

    order_totals.append(gross_total)

    return order_totals


def prepare_order_resource(customer, shipping_address, shipping_method, payment_address, payment_method):
    # Customer
    customer_firstname = customer.get('firstname', '')
    customer_lastname = customer.get('lastname', '')

    # Shipping Address
    shipping_address_name = shipping_address.get('name', '')
    shipping_address_address = shipping_address.get('address', '')
    shipping_address_city = shipping_address.get('city', '')
    shipping_address_postcode = shipping_address.get('postcode', '')

    # Shipping Method
    shipping_method_name = shipping_method.get('name', '')
    shipping_method_extension = shipping_method.get('extension', '')
    shipping_method_tax_class = shipping_method.get('tax_class', {})
    shipping_method_tax_class_name = shipping_method_tax_class.get(
        'name', '0 %')
    shipping_method_tax_class_tax_rate = shipping_method_tax_class.get('taxRates', [{}])[
        0].get('rate', '0.0000')

    # Payment Method
    payment_method_code = payment_method.get('code', '')

    # Creation Date
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Invoice Id
    timestamp = str(int(time.time()))[-8:]
    rand_num = str(random.randint(0, 999)).zfill(3)
    invoice_id = f"{timestamp}-{rand_num}"

    # Shipping Address 2
    shipping_address_address_2 = None

    # Handle GLS parcel shipping
    if shipping_method_extension == 'GLSPARCELLOCKER':
        shipping_address_address_2 = shipping_address_name
        shipping_method_name = f"{shipping_method_name} - {shipping_method_extension} - {shipping_address_name}"

    return {
        "invoiceId": invoice_id,
        "invoicePrefix": "AGENT",
        "firstname": customer.get('firstname', ''),
        "lastname": customer.get('lastname', ''),
        "phone": customer.get('telephone', ''),
        "fax": None,
        "email": customer.get('email', ''),
        "shippingFirstname": shipping_address.get('firstname', customer_firstname),
        "shippingLastname": shipping_address.get('lastname', customer_lastname),
        "shippingCompany": None,
        "shippingAddress1": shipping_address_address,
        "shippingAddress2": shipping_address_address_2,
        "shippingCity": shipping_address_city,
        "shippingPostcode": shipping_address_postcode,
        "shippingZoneName": None,
        "shippingCountryName": "Hungary",
        "shippingAddressFormat": None,
        "shippingMethodName": shipping_method_name,
        "shippingMethodTaxRate": shipping_method_tax_class_tax_rate,
        "shippingMethodTaxName": shipping_method_tax_class_name,
        "shippingMethodExtension": shipping_method.get('extension', ''),
        "shippingReceivingPointId": "0",
        "paymentFirstname": payment_address.get('firstname', customer_firstname),
        "paymentLastname": payment_address.get('lastname', customer_lastname),
        "paymentCompany": None,
        "paymentAddress1": payment_address.get('address', shipping_address_address),
        "paymentAddress2": None,
        "paymentCity": payment_address.get('city', shipping_address_city),
        "paymentPostcode": payment_address.get('postcode', shipping_address_postcode),
        "paymentZoneName": None,
        "paymentCountryName": "Hungary",
        "paymentAddressFormat": None,
        "paymentMethodName": payment_method.get('name', ''),
        "paymentMethodCode": payment_method_code,
        "paymentMethodTaxRate": "27.0000",
        "paymentMethodTaxName": "27 %",
        "paymentMethodAfter": "1" if payment_method_code.lower() == 'cod' else "0",
        "comment": "!!!!EZ EGY TESZT RENDELÉS!!!!",
        "total": None,
        "value": "1.00000000",
        "couponTaxRate": "-1.0000",
        "dateCreated": current_time,
        "dateUpdated": current_time,
        # "ip": "11.11.11.11",
        "pickPackPontShopCode": "",
        "customer": {
            "id": customer.get('id', '')
        },
        "customerGroup": {
            "id": "Y3VzdG9tZXJHcm91cC1jdXN0b21lcl9ncm91cF9pZD04"
        },
        "shippingZone": None,
        "shippingCountry": {
            "id": "Y291bnRyeS1jb3VudHJ5X2lkPTk3"
        },
        "paymentZone": None,
        "paymentCountry": {
            "id": "Y291bnRyeS1jb3VudHJ5X2lkPTk3"
        },
        "orderStatus": {
            "id": "b3JkZXJTdGF0dXMtb3JkZXJfc3RhdHVzX2lkPTE="
        },
        "language": {
            "id": "bGFuZ3VhZ2UtbGFuZ3VhZ2VfaWQ9MQ=="
        },
        "currency": {
            "id": "Y3VycmVuY3ktY3VycmVuY3lfaWQ9NA=="
        },
        "shippingMode": {
            "id": shipping_method.get('id', '')
        }
    }


async def create_order_resource(order_resource):
    return await call_shoprenter_api(method='POST', endpoint='orders', data=order_resource)
