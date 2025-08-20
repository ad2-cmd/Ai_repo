
import json
from typing import Dict
from fastmcp import Context
from mcp_utils.session import SessionManager
import uuid


class PaymentAddressTools:
    @classmethod
    async def parse_payment_address(cls, ctx: Context, lastname: str, firstname: str, postcode: str, city: str, address: str, telephone: str):
        session_manager = SessionManager().get_session(ctx.session_id)
        session_manager.found_addresses.append({
            'id': uuid.uuid4(),
            'lastname': lastname,
            'firstname': firstname,
            'postcode': postcode,
            'city': city,
            'address': address,
            'telephone': telephone
        })

    @classmethod
    async def store_selected_payment_address(cls, ctx: Context, payment_address_id: str):
        """
        Stores the selected payment address into the session
        """
        session_manager = SessionManager().get_session(ctx.session_id)
        payment_addresses = session_manager.found_addresses

        selected_payment_address = [
            payment_address for payment_address in payment_addresses if payment_address.get('id', '') == payment_address_id
        ]

        if not selected_payment_address:
            return {
                "status": "unsuccessfull",
                "payment_address_id": payment_address_id
            }

        session_manager.payment_address = selected_payment_address[0]

        return {
            "status": "successfull",
            "payment_address_id": session_manager.payment_address.get('id', '')
        }
