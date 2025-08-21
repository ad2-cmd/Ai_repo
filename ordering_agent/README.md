# 🛍️Premium Horse Feed

This is a simple MCP (Model Context Protocol) server that facilitates order management by connecting to product and customer databases. It exposes tools that an LLM can use to fetch product details, customer information, and create orders via a chat platform.

It uses the [FastMCP](https://github.com/chain-ml/model-context-protocol) library and `httpx` to fetch live data and manage orders via a standardized protocol that works seamlessly with LLMs and AI agents.

## 🚀 Features

- Get detailed info about any product
- Fetch customer information
- Create orders via chat platform
- Manage order status

## 📦 Requirements

- Python 3.8+
- Node.js (for some LLM hosts that require it)
- `httpx`
- `mcp` (Model Context Protocol library)

## ⚙️ Installation

# Create a new directory for our project

uv init order_management
cd order_management

# Create virtual environment and activate it

uv venv
.venv\Scripts\activate # On Windows

# source .venv/bin/activate # On macOS/Linux

# Install dependencies

uv add mcp[cli] httpx

# Create our server file

new-item order_management.py # On PowerShell
