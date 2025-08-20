

import json
from fastmcp.server.middleware import Middleware, MiddlewareContext

from mcp_utils.session import SessionManager


class SessionMiddleware(Middleware):

    async def on_get_prompt(self, context: MiddlewareContext, call_next):
        return await self.provide_session_state_for_request(context, call_next)

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        return await self.provide_session_state_for_request(context, call_next)

    async def provide_session_state_for_request(self, context: MiddlewareContext, call_next):

        print(f"Current message with print: {context.message}")

        if not context.fastmcp_context:
            print("No fastmcp_context")
            return await call_next(context)

        if not context.fastmcp_context.session_id:
            print("No session id")
            return await call_next(context)

        session_id = context.fastmcp_context.session_id
        session_manager = SessionManager().get_session(session_id)

        print(
            f"My own session: {json.dumps(session_manager.dump_session(), indent=4)}")

        return await call_next(context)
