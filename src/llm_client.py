"""
Shared Ollama client factory.

Reads OLLAMA_BASE_URL and OLLAMA_API_KEY from the environment and returns
a configured `ollama.Client` that works for both local and cloud Ollama.
"""

import os
import logging
from dotenv import load_dotenv
from ollama import Client

# Load .env every time this module is imported (picks up changes on Streamlit re-run)
load_dotenv(override=True)

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_ollama_client() -> Client:
    """Return a singleton Ollama client configured from env vars."""
    global _client
    if _client is not None:
        return _client

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    api_key = os.getenv("OLLAMA_API_KEY", "")

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    logger.info(f"🔗 Initialising Ollama client → {base_url} (auth={'yes' if api_key else 'no'})")
    _client = Client(host=base_url, headers=headers)
    return _client
