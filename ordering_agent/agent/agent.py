import json
import os
import re
from typing import Dict
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, SecretStr
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
import mcp_use
import uvicorn
import time
import random
import httpx
from utils.prompts import get_base_system_prompt, get_customer_identification_system_prompt, get_order_confirmation_system_prompt, get_order_finalization_system_prompt, get_payment_address_selection_system_prompt, get_payment_method_selection_system_prompt, get_product_selection_system_prompt, get_router_system_prompt, get_shipping_address_selection_system_prompt, get_shipping_method_selection_system_prompt, get_system_prompts

# --- Configuration ---

# Set MCP debug level (0: off, 1: info, 2: verbose)
mcp_use.set_debug(2)

# Load environment variables from .env file
load_dotenv()

# This client will be reused for all outgoing HTTP requests from the server.
timeout = httpx.Timeout(120)
async_http_client = httpx.AsyncClient(timeout=timeout)

mcp_server_base = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

SYSTEM_PROMPTS = get_system_prompts()
BASE_SYSTEM_PROMPT = get_base_system_prompt(SYSTEM_PROMPTS)
CUSTOMER_IDENTIFICATION_SYSTEM_PROMPT = get_customer_identification_system_prompt(
    SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
PRODUCT_SELECTION_SYSTEM_PROMPT = get_product_selection_system_prompt(
    SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
SHIPPING_METHOD_SELECTION_SYSTEM_PROMPT = get_shipping_method_selection_system_prompt(
    SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
SHIPPING_ADDRESS_SELECTION_SYSTEM_PROMPT = get_shipping_address_selection_system_prompt(
    SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
PAYMENT_ADDRESS_SELECTION_SYSTEM_PROMPT = get_payment_address_selection_system_prompt(
    SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
PAYMENT_METHOD_SELECTION_SYSTEM_PROMPT = get_payment_method_selection_system_prompt(
    SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
ORDER_CONFIRMATION_SYSTEM_PROMPT = get_order_confirmation_system_prompt(
    SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
ORDER_FINALIZATION_SYSTEM_PROMPT = get_order_finalization_system_prompt(
    SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
ROUTER_SYSTEM_PROMPT = get_router_system_prompt(SYSTEM_PROMPTS)

# CART_SYSTEM_PROMPT = get_cart_system_prompt(SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
# PAYMENT_SHIPPING_SYSTEM_PROMPT = get_payment_shipping_system_prompt(
#     SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
# ORDER_SYSTEM_PROMPT = get_order_system_prompt(
#     SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)

session_id_states = {}


def generate_session_id():
    timestamp = int(time.time() * 1000)  # Current time in milliseconds
    random_hex = hex(random.getrandbits(64))[2:]  # 64 random bits as hex
    return f"{timestamp:x}-{random_hex}"


async def get_current_session_state(session_id: str):
    try:
        response = await async_http_client.get(
            f"{mcp_server_base}/session_manager/session/{session_id}",
        )
        # It's good practice to check if the request was successful
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        print(f"Error fetching session state for {session_id}: {e}")
        # Return a default state or re-raise the exception
        return {"order_state": "default", "error": str(e)}


async def set_current_session_state(session_id: str, order_state: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{mcp_server_base}/session_manager/session/{session_id}",
                json={"order_state": order_state},  # send updated state
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        print(f"Error updating session state for {session_id}: {e}")
        return {"order_state": "default", "error": str(e)}
    except httpx.HTTPStatusError as e:
        print(
            f"Unexpected status updating session {session_id}: {e.response.status_code}")
        return {"order_state": "default", "error": str(e)}


# session_id = generate_session_id()


# --- Agent Initialization ---


class Agent:
    name: str
    session_id: str
    system_prompt: str
    client: MCPClient
    llm: ChatOpenAI
    agent: MCPAgent

    def __init__(
        self,
        name: str = "default",
        session_id: str = "default",
        system_prompt: str = "You are a helpful AI Assistant professional in customer service and helping customers make orders in a webshop in Hungarian",
        model: str = "openai/gpt-4o-mini",
        memory_enabled: bool = True,
        temperature: float | None = None
    ) -> None:
        client_config = {
            "mcpServers": {
                "premium-horse-feeds-mcp-server": {
                    "transport": "http",
                    "url": f"{mcp_server_base}/mcp/",
                    "headers": {"mcp-session-id": session_id}
                }
            }
        }
        self.client = MCPClient.from_dict(client_config)

        # Initialize the Language Model
        self.llm = ChatOpenAI(
            api_key=SecretStr(os.getenv("OPENROUTER_API_KEY") or ""),
            base_url=os.getenv("OPENROUTER_BASE_URL"),
            model=model,
            temperature=temperature
        )

        # Create a single, reusable agent instance
        # Note: For a multi-user application, you would manage separate agent instances per user session.
        # For this simple UI, we use one global agent.
        agent = MCPAgent(
            llm=self.llm,
            client=self.client,
            max_steps=10,
            verbose=True,
            system_prompt=system_prompt,
            memory_enabled=memory_enabled
        )

        self.name = name
        self.session_id = session_id
        self.agent = agent

    def clear_conversation_history(self):
        return self.agent.clear_conversation_history()

    async def run(self, query: str):
        return await self.agent.run(query)

    async def list_tools(self):
        await self.client.create_all_sessions(auto_initialize=True)
        mcp_session = self.client.get_session('premium-horse-feeds-mcp-server')
        tools = await mcp_session.list_tools()
        # await mcp_session.disconnect()
        return tools


class Agents:
    agents: Dict[str, Dict[str, Agent]]

    def __init__(self):
        self.agents = {}

    def create_or_get_agent(
        self,
        session_id: str = "default",
        name: str = "default",
        system_prompt: str = "You are a helpful AI Assistant professional in customer service and helping customers make orders in a webshop in Hungarian",
        model: str = "openai/gpt-4o-mini",
        memory_enabled: bool = True,
        temperature: float | None = None
    ):
        # conversation_history = []
        agent = self.get_agent(session_id, name)
        if agent is not None:
            return agent
            # conversation_history = agent.agent.get_conversation_history()

        agent = Agent(
            name=name,
            session_id=session_id,
            system_prompt=system_prompt,
            model=model,
            memory_enabled=memory_enabled,
            temperature=temperature
        )

        # for history in conversation_history:
        #     agent.agent.add_to_history(history)

        self.agents.setdefault(session_id, {})[name] = agent
        return agent

    def get_agent(self, session_id: str = "default", name: str = "default"):
        return self.agents.get(session_id, {}).get(name, None)


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
    agent: str


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
    global SYSTEM_PROMPTS
    global BASE_SYSTEM_PROMPT
    global CUSTOMER_IDENTIFICATION_SYSTEM_PROMPT
    global PRODUCT_SELECTION_SYSTEM_PROMPT
    global SHIPPING_METHOD_SELECTION_SYSTEM_PROMPT
    global SHIPPING_ADDRESS_SELECTION_SYSTEM_PROMPT
    global PAYMENT_ADDRESS_SELECTION_SYSTEM_PROMPT
    global PAYMENT_METHOD_SELECTION_SYSTEM_PROMPT
    global ORDER_CONFIRMATION_SYSTEM_PROMPT
    global ORDER_FINALIZATION_SYSTEM_PROMPT
    global ROUTER_SYSTEM_PROMPT
    global session_id_states

    # global CART_SYSTEM_PROMPT
    # global PAYMENT_SHIPPING_SYSTEM_PROMPT
    # global ORDER_SYSTEM_PROMPT

    session_id_exists = session_id_states.get(session_id, {"exists": False})

    if not session_id_exists.get('exists'):
        SYSTEM_PROMPTS = get_system_prompts()
        BASE_SYSTEM_PROMPT = get_base_system_prompt(SYSTEM_PROMPTS)
        CUSTOMER_IDENTIFICATION_SYSTEM_PROMPT = get_customer_identification_system_prompt(
            SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
        PRODUCT_SELECTION_SYSTEM_PROMPT = get_product_selection_system_prompt(
            SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
        SHIPPING_METHOD_SELECTION_SYSTEM_PROMPT = get_shipping_method_selection_system_prompt(
            SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
        SHIPPING_ADDRESS_SELECTION_SYSTEM_PROMPT = get_shipping_address_selection_system_prompt(
            SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
        PAYMENT_ADDRESS_SELECTION_SYSTEM_PROMPT = get_payment_address_selection_system_prompt(
            SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
        PAYMENT_METHOD_SELECTION_SYSTEM_PROMPT = get_payment_method_selection_system_prompt(
            SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
        ORDER_CONFIRMATION_SYSTEM_PROMPT = get_order_confirmation_system_prompt(
            SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
        ORDER_FINALIZATION_SYSTEM_PROMPT = get_order_finalization_system_prompt(
            SYSTEM_PROMPTS, BASE_SYSTEM_PROMPT)
        ROUTER_SYSTEM_PROMPT = get_router_system_prompt(SYSTEM_PROMPTS)

    session_id_states[session_id] = {"exists": True}

    session_data = await get_current_session_state(session_id)
    print("Session data:", json.dumps(session_data))

    router_system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{ROUTER_SYSTEM_PROMPT}"

    router_system_prompt = router_system_prompt.replace('{', '{{')
    router_system_prompt = router_system_prompt.replace('}', '}}')

    router_agent = agents.create_or_get_agent(
        session_id,
        name='router_agent',
        system_prompt=router_system_prompt,
        memory_enabled=False,
        temperature=0.1
        # model="openai/gpt-4o-mini"
    )

    router_agent.agent.clear_conversation_history()

    agent_list = agents.agents.get(session_id, {}).items()

    conversation_history = """
    Conversation history:

    """

    for agent_name, agent in agent_list:
        agent_history = agent.agent.get_conversation_history()
        for conversation in agent_history:
            conversation_history += f"{conversation.content}\n"

    result_order_state = await router_agent.run(f"{conversation_history}\n{request.message}")

    result_order_state = result_order_state.replace(
        "```", "").replace("\n", "").replace("\t", "").replace("(", "").replace(")", "").replace("$", "")

    print("Router Agent Result Order State")
    print(result_order_state)

    session_data = await set_current_session_state(session_id, result_order_state)

    order_state = session_data.get('order_state', 'default')
    system_prompt = BASE_SYSTEM_PROMPT
    agent_name = 'information_gathering_agent'

    if order_state == 'customer_identification':
        system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{CUSTOMER_IDENTIFICATION_SYSTEM_PROMPT}"
        agent_name = 'customer_identification_agent'
    if order_state == 'product_selection':
        system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{PRODUCT_SELECTION_SYSTEM_PROMPT}"
        agent_name = 'product_selection_agent'
    if order_state == 'shipping_method_selection':
        system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{SHIPPING_METHOD_SELECTION_SYSTEM_PROMPT}"
        agent_name = 'shipping_method_selection_agent'
    if order_state == 'shipping_address_selection':
        system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{SHIPPING_ADDRESS_SELECTION_SYSTEM_PROMPT}"
        agent_name = 'shipping_address_selection_agent'
    if order_state == 'payment_address_selection':
        system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{PAYMENT_ADDRESS_SELECTION_SYSTEM_PROMPT}"
        agent_name = 'payment_address_selection_agent'
    if order_state == 'payment_method_selection':
        system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{PAYMENT_METHOD_SELECTION_SYSTEM_PROMPT}"
        agent_name = 'payment_method_selection_agent'
    if order_state == 'order_confirmation':
        system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{ORDER_CONFIRMATION_SYSTEM_PROMPT}"
        agent_name = 'order_confirmation_agent'
    if order_state == 'order_finalization':
        system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{ORDER_FINALIZATION_SYSTEM_PROMPT}"
        agent_name = 'order_finalization_agent'

    # if order_state == 'customer_identification' or order_state == 'product_selection':
    #     system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{CART_SYSTEM_PROMPT}"
    #     agent_name = 'cart_agent'
    # if order_state == 'shipping_method_selection' or order_state == 'shipping_address_selection' or order_state == 'payment_address_selection' or order_state == 'payment_method_selection':
    #     system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{PAYMENT_SHIPPING_SYSTEM_PROMPT}"
    #     agent_name = 'payment_shipping_agent'
    # if order_state == 'order_confirmation' or order_state == 'order_finalization':
    #     system_prompt = f"Order State: {json.dumps(session_data, indent=2)}\n{ORDER_SYSTEM_PROMPT}"
    #     agent_name = 'order_agent'

    system_prompt = system_prompt.replace('{', '{{')
    system_prompt = system_prompt.replace('}', '}}')

    agent = agents.create_or_get_agent(
        session_id,
        name=agent_name,
        system_prompt=system_prompt,
        # model="openai/gpt-4o-mini"
    )

    if not agent:
        return ChatResponse(reply="Sajnálom, valami hiba lépett fel a webshop ügynök indításában", agent='')

    # tools = await agent.list_tools()
    # tools_to_disallow = []
    # for tool in tools:
    #     tool_meta = tool.meta or {}
    #     tool_tags = tool_meta.get('_fastmcp', {}).get('tags', {})
    #     if agent_name in tool_tags:
    #         continue
    #
    #     tools_to_disallow.append(tool.name)
    #
    # print("Disallowed tools list")
    # print(tools_to_disallow)
    #
    # agent.agent.set_disallowed_tools(tools_to_disallow)

    print()

    # Get session data from mcp server
    print(f"Session data: {session_data}")

    # final_query = f"""
    #     A session állapota és a felhasználói üzenet alapján határozd meg a rendelési folyamat következő lépését.
    #     Azonosítsd:
    #         1. Milyen adatok hiányoznak a rendelés folytatásához.
    #         2. Milyen adatok már rendelkezésre állnak.
    #
    #     Ezen információk alapján döntsd el, mely eszköz(ök) meghívása szükséges a felhasználó segítéséhez, hogy eljusson a rendelés leadásáig és hívd is meg a szükséges eszközöket, promptokat, hogy a beszélgetés ne álljon le egészen a rendelés leadásáig.
    #
    #     Jelenlegi session állapot:
    #     {json.dumps(session_data, indent=2)}
    #
    #     Felhasználói üzenet:
    #     {request.message}
    # """
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

    return ChatResponse(reply=final_result, agent=agent_name)


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
