
import json
from typing import Dict
from fastmcp import Context
from mcp_utils.session import SessionManager
import uuid


class PaymentAddressTools:
    @classmethod
    async def parse_payment_address(cls, ctx: Context, lastname: str, firstname: str, postcode: str, city: str, address: str, telephone: str):
        session_manager = SessionManager().get_session(ctx.session_id)
        session_manager.found_addresses = [{
            'id': uuid.uuid4(),
            'lastname': lastname,
            'firstname': firstname,
            'postcode': postcode,
            'city': city,
            'address': address,
            'telephone': telephone
        }]


    @classmethod
    async def store_selected_payment_address(cls, ctx: Context, payment_address_id: str):
        """
        Stores the selected payment address into the session
        """
        session_manager = SessionManager().get_session(ctx.session_id)
        shipping_addresses = session_manager.found_addresses

        selected_shipping_address = [
            shipping_address for shipping_address in shipping_addresses if shipping_address.get('id', '') == payment_address_id
        ]

        if not selected_shipping_address:
            return {
                "status": "unsuccessfull",
                "payment_address_id": payment_address_id
            }

        session_manager.shipping_address = selected_shipping_address[0]

        return {
            "status": "successfull",
            "payment_address_id": session_manager.shipping_address.get('id', '')
        }
