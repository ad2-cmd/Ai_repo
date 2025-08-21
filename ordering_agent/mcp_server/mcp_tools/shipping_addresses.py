
import json
from typing import Dict
from fastmcp import Context
from mcp_utils.session import SessionManager


class ShippingAddressTools:
    @classmethod
    async def store_selected_shipping_address(cls, ctx: Context, shipping_address_id: str):
        """
        Stores the selected shipping address into the session
        """
        session_manager = SessionManager().get_session(ctx.session_id)
        shipping_addresses = session_manager.found_addresses

        selected_shipping_address = [
            shipping_address for shipping_address in shipping_addresses if shipping_address.get('id', '') == shipping_address_id
        ]

        if not selected_shipping_address:
            return {
                "status": "unsuccessfull",
                "shipping_address_id": shipping_address_id
            }

        session_manager.shipping_address = selected_shipping_address[0]

        return {
            "status": "successfull",
            "shipping_address_id": session_manager.shipping_address.get('id', '')
        }
