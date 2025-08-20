import json
from fastmcp import Context
from fastmcp.prompts.prompt import Message
from mcp_tools.shipping_methods import ShippingMethodTools
from mcp_utils.session import SessionManager
from mcp_utils.shipping_method import search_shipping_methods


class ShippingMethodPrompts:
    @classmethod
    async def list_shipping_methods(cls, ctx: Context):
        """
        Shows the customer a list of available shipping methods and prompts them to choose one when the customer doesn't know which shipping method to use.

        This prompt is used to display the available shipping methods to the customer and ask them to select their preferred option.
        The shipping methods are presented as a numbered list.
        """

        shipping_methods = await ShippingMethodTools.get_shipping_methods()
        session_manager = SessionManager().get_session(ctx.session_id)
        session_manager.found_shipping_methods = shipping_methods

        shipping_methods_json = []
        for method in shipping_methods:
            shipping_method_json = {
                "id": method.id,
                "name": method.name,
                "description": method.description
            }
            shipping_methods_json.append(shipping_method_json)

        response = f"""
        ## Task
        Extract and return all available shipping methods from the input JSON.
        Return ONLY the following fields for each shipping method:
            - id
            - name
            - description
        
        ALWAYS include the id when listing the shipping methods and do NOT modify anything on the id!

        ## Input
        {json.dumps(shipping_methods_json, indent=4)}

        ## Output
        Return a list of the shipping methods in this format and ask which shipping method would the user/customer choose by choosing a serial number or the name of the shipping method:
            1.
                ID: id
                Név: name
                Leírás: description
            2.
                ID: id
                Név: name
                Leírás: description
            3.
                ...
        """

        # response = "Válaszd ki a szállítási módot:\n\n"
        # for i, method in enumerate(shipping_methods):
        #     response += f"{i + 1}.\n"
        #     response += f"  ID: {method.id}\n"
        #     response += f"  Név: {method.name}\n"
        #
        # response += "\nKérlek add meg a választott szállítási mód sorszámát."

        return Message(response, role="user")

    @classmethod
    async def select_shipping_method_by_name(cls, ctx: Context, shipping_method_name: str):
        """
        Let's the customer choose a shipping method by name

        Use this prompt when the customer has already decided on what shipping method to use and prompts you to use that. This prompt is only to ask back the customer if the found shipping method is the correct one.

        This prompt is used to make sure the correct shipping method is chosen by the customer by asking back if the found shipping method is the one the customer wanted to use
        """

        shipping_methods = await search_shipping_methods(shipping_method_name)
        session_manager = SessionManager().get_session(ctx.session_id)
        session_manager.found_shipping_methods = shipping_methods

        shipping_methods_json = []
        for method in shipping_methods:
            shipping_method_json = {
                "id": method.id,
                "name": method.name,
                "description": method.description
            }
            shipping_methods_json.append(shipping_method_json)

        response = f"""
        ## Task
        Extract and return ONLY that shipping method that is the MOST RELEVANT to the original customer query from the input JSON.
        Return ONLY the following fields for the most relevant shipping method:
            - id
            - name
            - description

        ALWAYS include the id when listing the shipping methods and do NOT modify anything on the id!

        ## Input
        {json.dumps(shipping_methods_json, indent=4)}

        ## Output
        Return the only shipping method in this format and ask if this is what the customer wanted to select and use:
            ID: id
            Név: name
            Leírás: description
        """

        return Message(response, role="user")
