import json
from random import random
from fastmcp import Context
from fastmcp.prompts.prompt import Message

from mcp_utils.session import SessionManager


class PaymentAddressPrompts:
    @classmethod
    async def customer_address_selection(cls, ctx: Context):
        """
        Presents the customer with a list of addresses to choose from.

        This prompt is used when multiple addresses are found for the customer.
        It displays the addresses and asks the customer to choose one.
        """
        session_manager = SessionManager().get_session(ctx.session_id)
        addresses = session_manager.customer.get('addresses', [])
        session_manager.found_addresses = addresses

        if len(addresses) == 0:
            return Message('Nem találtam a felhasználódhoz kapcsolódó címeket', role="user")

        response = f"""
        ## Task
        Extract and return all found addresses from the input JSON.
        Return ONLY the following fields for each address:
            - id
            - lastname
            - firstname
            - postcode
            - city
            - address
            - telephone

        ALWAYS include the id when listing the addresses and do NOT modify anything on the id!

        ## Input
        {json.dumps(addresses, indent=4)}

        ## Output
        Return a list of the addresses in this format and ask which address would the user/customer choose by choosing the serial number or by other details of the address, such as postcode, city, address or telephone:
            1.
                ID: id
                Vezetéknév: lastname
                Keresztnév: firstname
                Irányítószám: postcode
                Város: city
                Cím: address (mask this value with #)
                Telefon: telephone (mask this value with #)
            2.
                ID: id
                Vezetéknév: lastname
                Keresztnév: firstname
                Irányítószám: postcode
                Város: city
                Cím: address (mask this value with #)
                Telefon: telephone (mask this value with #)
            3.
                ...
        """

        return Message(response, role="user")

    @classmethod
    async def ask_for_new_payment_address(cls):
        """
        Ask for a new payment address from the customer if there is no address found for the found customer.

        This prompt is used when the customer wants to enter a new payment address.
        It provides a format for the customer to follow.
        """
        return Message("""Kérlek, add meg a számlázási címet a következő formátumban:
    Vezetéknév, Keresztnév, Irányítószám, Város, Utca és házszám, Telefonszám

    Példa: Kovács, János, 1234, Budapest, Fő utca 1, +36301234567""", role="user")
