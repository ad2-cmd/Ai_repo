

import json
from fastmcp import Context
from fastmcp.prompts.prompt import Message

from mcp_utils.session import SessionManager
from mcp_utils.shipping_addresses import search_gls_parcel_machines


class ShippingAddressPrompts:
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
    async def request_close_location_to_gls_parcel_machine(cls):
        """Requests an address that is close to the location of the GLS parcel machine where the customer wants to order his/her package when the customer chose to use GLS parcel machine shipping method"""
        return Message("""Adjon meg egy konkrét címet, várost vagy irányítószámot, amely a legközelebb van a GLS csomagautomatához amelybe rendelni szeretné a csomagját.""", role="user")

    @classmethod
    async def gls_parcel_machine_location_selection(cls, ctx: Context, address_close_to_gls_parcel_machine: str):
        """
        Presents the customer with a list of GLS parcel machine addresses to choose from.

        This prompt is used when the customer chooses to use GLS parcel machine shipping method and provided an address close to a GLS parcel machine's location
        """

        gls_parcel_machines = await search_gls_parcel_machines(
            address_close_to_gls_parcel_machine)

        session_manager = SessionManager().get_session(ctx.session_id)
        session_manager.found_addresses = gls_parcel_machines

        response = f"""
        ## Task
        Extract and return all found addresses from the input JSON.
        Return ONLY the following fields for each address:
            - id
            - name
            - postcode
            - city
            - address

        ALWAYS include the id when listing the addresses and do NOT modify anything on the id!

        ## Input
        {json.dumps(gls_parcel_machines, indent=4)}

        ## Output
        Return a list of the addresses in this format and ask which address would the user/customer choose by choosing the serial number or by other details of the address, such as postcode, city, address or telephone:
            1.
                ID: id
                Név: name
                Irányítószám: postcode
                Város: city
                Cím: address
            2.
                ID: id
                Név: name
                Irányítószám: postcode
                Város: city
                Cím: address
            3.
                ...
        """

        return Message(response, role="user")

    @classmethod
    async def customer_request_new_address(cls):
        """
        Requests a new shipping address from the customer if there is no address found for the found customer.

        This prompt is used when the customer wants to enter a new shipping address.
        It provides a format for the customer to follow.
        """
        return Message("""Kérlek, add meg a szállítási címet a következő formátumbarole="user":
    Vezetéknév, Keresztnév, Irányítószám, Város, Utca és házszám, Telefonszám, Ország

    Példa: Kovács, János, 1234, Budapest, Fő utca 1, +36301234567, Magyarország""", role="user")
