import time
import random
import httpx
import os

timeout = httpx.Timeout(120)
async_http_client = httpx.AsyncClient(timeout=timeout)

mcp_server_base = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

# NOTE: this function is not used anywhere right now
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