import json
from fastmcp import Context
from fastmcp.prompts.prompt import Message

from mcp_tools.payment_methods import PaymentMethodTools
from mcp_utils.session import SessionManager


class PaymentMethodPrompts:
    @classmethod
    async def list_payment_methods(cls, ctx: Context):
        """
        Presents the customer with a list of available payment methods and prompts them to choose one.

        This prompt is used to display the available payment methods to the customer and ask them to select their preferred option.
        The payment methods are presented as a numbered list, with each item including the payment method's name and description.
        """

        payment_methods = await PaymentMethodTools.get_payment_methods()
        session_manager = SessionManager().get_session(ctx.session_id)
        session_manager.found_payment_methods = payment_methods

        payment_methods_json = []
        for method in payment_methods:
            payment_method_json = {
                "id": method.id,
                "name": method.name,
                "description": method.description
            }
            payment_methods_json.append(payment_method_json)

        response = f"""
        ## Task
        Extract and return all available payment methods from the input JSON.
        Return ONLY the following fields for each payment method:
            - id
            - name
            - description

        ALWAYS include the id when listing the payment methods and do NOT modify anything on the id!

        ## Input
        {json.dumps(payment_methods_json, indent=4)}

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

        # response = "Válaszd ki a fizetési módot:\n\n"
        # for i, method in enumerate(payment_methods):
        #     response += f"{i + 1}.\n"
        #     response += f"  ID: {method.id}\n"
        #     response += f"  Név: {method.name}\n"
        #     response += f"  Leírás: {method.description}\n"
        #
        # response += "\nAdd meg a választott fizetési mód sorszámát."

        return Message(response, role="user")
