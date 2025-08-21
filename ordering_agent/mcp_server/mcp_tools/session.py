from fastmcp import Context
from mcp_utils.session import OrderStateLiteral, SessionManager


class SessionTools:
    @classmethod
    async def set_order_state(cls, ctx: Context, order_state: OrderStateLiteral):
        """
        Used to set order state based on what the user/customer wants to do next
        """
        session_manager = SessionManager().get_session(ctx.session_id)
        session_manager.order_state = order_state

        return session_manager.order_state

    @classmethod
    async def get_order_state(cls, ctx: Context):
        """
        Used to get order state. It contains a list of what is missing and what is still needed
        """
        session_manager = SessionManager().get_session(ctx.session_id)
        return session_manager.get_missing_data_types()
