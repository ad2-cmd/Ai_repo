from fastmcp import Context
from mcp_utils.customers import search_customer
from mcp_utils.session import SessionManager


class CustomerTools:
    @classmethod
    async def search_customer_by_email(cls, ctx: Context, email_address: str):
        """
        Get's custmer details by the customer's email address

        This tool is used to get customer details by the customer's email address.
        It returns a structured object containing the customer's details.
        """
        customer = await search_customer(email_address)

        if not customer:
            return {"status": "not found"}

        session_manager = SessionManager().get_session(ctx.session_id)
        session_manager.found_customer = customer

        return {
            "status": "found",
            "customer": customer
        }

    @classmethod
    async def customer_agreed_with_found_details(cls, ctx: Context):
        """
        Saves customer details to the session after customer agreed the details are ok
        """
        session_manager = SessionManager().get_session(ctx.session_id)
        session_manager.customer = session_manager.found_customer

        return {
            "status": "successfully saved customer details",
            "customer_id": session_manager.customer.get('id'),
            "customer_name": session_manager.customer.get('name')
        }
