from dotenv import load_dotenv
import mcp_use
import httpx
import os
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
from pydantic import SecretStr
from typing import Dict
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

# --- Configuration ---

# Set MCP debug level (0: off, 1: info, 2: verbose)
mcp_use.set_debug(2)

# Load environment variables from .env file
load_dotenv()

# This client will be reused for all outgoing HTTP requests from the server.
timeout = httpx.Timeout(120)
async_http_client = httpx.AsyncClient(timeout=timeout)

mcp_server_base = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

BASE_SYSTEM_PROMPT = get_base_system_prompt()
CUSTOMER_IDENTIFICATION = get_customer_identification_prompt(
    BASE_SYSTEM_PROMPT)
PRODUCT_SELECTION = get_product_selection_prompt(BASE_SYSTEM_PROMPT)
SHIPPING_METHOD = get_shipping_method_prompt(BASE_SYSTEM_PROMPT)
SHIPPING_ADDRESS = get_shipping_address_prompt(BASE_SYSTEM_PROMPT)
PAYMENT_METHOD = get_payment_method_prompt(BASE_SYSTEM_PROMPT)
ORDER_CONFIRMATION = get_order_confirmation_prompt(BASE_SYSTEM_PROMPT)
ORDER_FINALIZATION = get_order_finalization_prompt(BASE_SYSTEM_PROMPT)

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
        model: str = "openai/gpt-4o-mini"
    ) -> None:
        client_config = {
            "mcpServers": {
                "http": {
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
        )

        # Create a single, reusable agent instance
        # Note: For a multi-user application, you would manage separate agent instances per user session.
        # For this simple UI, we use one global agent.
        agent = MCPAgent(
            llm=self.llm,
            client=self.client,
            max_steps=10,
            verbose=True,
            system_prompt=system_prompt
        )

        self.name = name
        self.session_id = session_id
        self.agent = agent

    def clear_conversation_history(self):
        return self.agent.clear_conversation_history()

    async def run(self, query: str):
        return await self.agent.run(query)


class Agents:
    agents: Dict[str, Dict[str, Agent]]

    def __init__(self):
        self.agents = {}

    def create_or_get_agent(
        self,
        session_id: str = "default",
        name: str = "default",
        system_prompt: str = "You are a helpful AI Assistant professional in customer service and helping customers make orders in a webshop in Hungarian",
        model: str = "openai/gpt-4o-mini"
    ):
        conversation_history = []
        agent = self.get_agent(session_id, name)
        if agent is not None:
            conversation_history = agent.agent.get_conversation_history()

        agent = Agent(name=name, session_id=session_id,
                      system_prompt=system_prompt, model=model)

        for history in conversation_history:
            agent.agent.add_to_history(history)

        self.agents.setdefault(session_id, {})[name] = agent
        return agent

    def create_agent(
        self,
        session_id: str = "default",
        name: str = "default",
        system_prompt: str = "You are a helpful AI Assistant professional in customer service and helping customers make orders in a webshop in Hungarian",
        model: str = "openai/gpt-4o-mini"
    ):
        agent = Agent(name=name, session_id=session_id,
                      system_prompt=system_prompt, model=model)
        self.agents.setdefault(session_id, {})[name] = agent
        return agent

    def get_agent(self, session_id: str = "default", name: str = "default"):
        return self.agents.get(session_id, {}).get(name, None)
    
