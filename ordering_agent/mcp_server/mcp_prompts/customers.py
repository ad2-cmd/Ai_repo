import json
from fastmcp import Context
from fastmcp.prompts.prompt import Message
from mcp_tools.customers import CustomerTools
from mcp_utils.session import SessionManager


class CustomerPrompts:
    @classmethod
    async def customer_identification(cls):
        """
        Initiates the customer identification workflow.

        This prompt is used to start the process of identifying the customer at the beginning of the order process.
        It asks the customer for their email address to begin the identification process.
        """
        response = """
        ## Task
        Ask for an email address the user/customer has already registered with

        ## Output
        A friendly message for the user/customer, prompting for information to start customer identification
        """

        # response = """Üdvözöllek a webshopban! Segítek leadni a rendelésedet. A rendelés leadásához először azonosítanom kell téged. Kérlek, add meg az email címedet, amivel regisztráltál."""

        return Message(response, role="user")

    @classmethod
    async def search_customer_by_email_address(cls, ctx: Context, email_address: str):
        """
        Confirms the customer's details after they have been found in the database.

        This prompt is used to confirm the customer's id, name, email, phone number and addresses with the customer.
        It asks the customer to confirm whether the details are correct.
        """

        await CustomerTools.search_customer_by_email(ctx, email_address)

        session_manager = SessionManager().get_session(ctx.session_id)
        customer = session_manager.found_customer

        if not customer:
            return Message("Hiba: Először azonosítani kell egy ügyfelet.", role="user")

        response = f"""
        ## Task
        Extract and return information from the input JSON.
        Return ONLY the following fields for the customer:
            - id
            - name
            - email
            - telephone

        ALWAYS include the id when listing the information about the customer and do NOT modify anything on the id!

        ## Input
        {json.dumps(customer, indent=4)}

        ## Output
        Return a question for the user/customer about the found data of the user/customer if the data is ok and list the found information in the following format:
            ID: id
            Név: name
            Email: email (mask this value with #)
            Telefon: telephone (mask this value with #)
        """

    #     response = f"""
    # Megtaláltalak az adatbázisban!
    # Ügyfél adatok:
    # - Név: {customer.get('name')}
    # - Email: {customer.get('email')}
    # - Telefon: {customer.get('telephone')}
    #
    # Ezek az adatok helyesek? (igen/nem)"""

        return Message(response, role="user")
