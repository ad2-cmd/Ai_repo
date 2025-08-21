from fastapi import APIRouter, FastAPI
from pydantic import BaseModel
from .agent import Agents
import json
import os
import re
import uvicorn
from starlette.middleware.cors import CORSMiddleware
import httpx
from utils.prompts import (
    get_base_system_prompt,
    get_customer_identification_prompt,
    get_order_confirmation_prompt,
    get_order_finalization_prompt,
    get_payment_method_prompt,
    get_product_selection_prompt,
    get_shipping_address_prompt,
    get_shipping_method_prompt
)
from .session import get_current_session_state

BASE_SYSTEM_PROMPT = get_base_system_prompt()
CUSTOMER_IDENTIFICATION = get_customer_identification_prompt(BASE_SYSTEM_PROMPT)
PRODUCT_SELECTION = get_product_selection_prompt(BASE_SYSTEM_PROMPT)
SHIPPING_METHOD = get_shipping_method_prompt(BASE_SYSTEM_PROMPT)
SHIPPING_ADDRESS = get_shipping_address_prompt(BASE_SYSTEM_PROMPT)
PAYMENT_METHOD = get_payment_method_prompt(BASE_SYSTEM_PROMPT)
ORDER_CONFIRMATION = get_order_confirmation_prompt(BASE_SYSTEM_PROMPT)
ORDER_FINALIZATION = get_order_finalization_prompt(BASE_SYSTEM_PROMPT)

session_id_states = {}

timeout = httpx.Timeout(120)
async_http_client = httpx.AsyncClient(timeout=timeout)
mcp_server_base = os.getenv("MCP_SERVER_URL", "http://localhost:8000")


# --- FastAPI Web Server ---

prefix_router = APIRouter(prefix="")

# Create the FastAPI agent_app
agent_app = FastAPI(
    title="MCP Chat Server",
    description="A backend server to connect the MCP Agent to a web UI.",
    version="1.0.0",
)


# --- API Endpoints ---

# Define the request data model
class ChatRequest(BaseModel):
    message: str
    session_id: str

# Define the response data model
class ChatResponse(BaseModel):
    reply: str


agents = Agents()


@prefix_router.get("/status")
def get_status():
    """Provides a simple endpoint to check if the server is running."""
    return {"status": "MCP Chat Server is running"}


@prefix_router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session data by id"""
    return await get_current_session_state(session_id)


@prefix_router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Endpoint to receive a user message and get a reply from the MCP Agent.
    """
    print(f"Received message: {request.message}")

    session_id = request.session_id

    # Make sure to use the global variables here
    global BASE_SYSTEM_PROMPT
    global CUSTOMER_IDENTIFICATION
    global PRODUCT_SELECTION
    global SHIPPING_METHOD
    global SHIPPING_ADDRESS
    global PAYMENT_METHOD
    global ORDER_CONFIRMATION
    global ORDER_FINALIZATION
    global session_id_states

    session_id_exists = session_id_states.get(session_id, {"exists": False})

    if not session_id_exists.get('exists'):
        BASE_SYSTEM_PROMPT = get_base_system_prompt()
        CUSTOMER_IDENTIFICATION = get_customer_identification_prompt(BASE_SYSTEM_PROMPT)
        PRODUCT_SELECTION = get_product_selection_prompt(BASE_SYSTEM_PROMPT)
        SHIPPING_METHOD = get_shipping_method_prompt(BASE_SYSTEM_PROMPT)
        SHIPPING_ADDRESS = get_shipping_address_prompt(BASE_SYSTEM_PROMPT)
        PAYMENT_METHOD = get_payment_method_prompt(BASE_SYSTEM_PROMPT)
        ORDER_CONFIRMATION = get_order_confirmation_prompt(BASE_SYSTEM_PROMPT)
        ORDER_FINALIZATION = get_order_finalization_prompt(BASE_SYSTEM_PROMPT)

    session_id_states[session_id] = {"exists": True}

    session_data = await get_current_session_state(session_id)
    print("Session data:", json.dumps(session_data))

    order_state = session_data.get('order_state', 'default')
    system_prompt = BASE_SYSTEM_PROMPT

    if (order_state == "customer_identification"):
        system_prompt = CUSTOMER_IDENTIFICATION
    elif (order_state == "product_selection"):
        system_prompt = PRODUCT_SELECTION
    elif (order_state == "shipping_method_selection"):
        system_prompt = SHIPPING_METHOD
    elif (order_state == "shipping_address_selection_or_new"):
        system_prompt = SHIPPING_ADDRESS
    elif (order_state == "payment_method_selection"):
        system_prompt = PAYMENT_METHOD
    elif (order_state == "order_confirmation"):
        system_prompt = ORDER_CONFIRMATION
    elif (order_state == "order_finalization"):
        system_prompt = ORDER_FINALIZATION

    agent = agents.create_or_get_agent(
        session_id,
        name="information_gathering_agent",
        system_prompt=system_prompt,
        # model="google/gemini-2.0-flash-001"
    )

    # Get session data from mcp server
    print(f"Session data: {session_data}")

    final_query = f"""
    Jelenlegi session állapot: {session_data}

    A folyamat amihez a megfelelő eszközöket vagy promptokat kell meghívnod: {session_data.get('order_state', '')}

    Felhasználói üzenet: {request.message}
    """
    final_query = request.message

    print(f"Final query: {final_query}")

    # Run the agent with the user's input
    result = await agent.run(final_query)

    print(f"Agent response: {result}")

    # The original script cleared history on every turn. For a continuous workflow,
    # this is likely not desired. The agent should maintain its own state.
    # If the conversation needs to be reset, a separate endpoint or logic should handle it.
    # agent.clear_conversation_history()

    # Replace with an <a> tag
    pattern = r'(https?://[^\s]+)'
    result = re.sub(pattern, r'<a href="\1" target="_blank">\1</a>', result)

    result = result.replace("*", "")
    final_result = re.sub(r'^.*ID:.*\n?', '', result, flags=re.MULTILINE)

    return ChatResponse(reply=final_result)


agent_app.include_router(prefix_router)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows the HTML file (running on a different origin) to make requests to this server.
agent_app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Main Execution ---

if __name__ == "__main__":
    # Run the server with uvicorn on port 8001
    print("Starting MCP Chat Server.")
    print("Access the UI at http://localhost:8001")
    print("Check server status at http://localhost:8001/status")
    uvicorn.run(agent_app, host="0.0.0.0", port=8001)
