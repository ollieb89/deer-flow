"""Kilocode API client.

Provides a simple client for interacting with the kilocode AI Gateway API.
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.kilo.ai/api/gateway"


class KilocodeClient:
    """Client for the kilocode AI Gateway API.
    
    Provides methods for fetching models and other gateway information.
    
    Example:
        >>> client = KilocodeClient(api_key="your-api-key")
        >>> models = await client.list_models()
        >>> print(f"Available models: {len(models)}")
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the kilocode client.
        
        Args:
            api_key: kilocode API key. If None, reads from KILO_API_KEY env var.
            base_url: Base URL for the kilocode API. Defaults to https://api.kilo.ai/api/gateway
            timeout: Request timeout in seconds.
            
        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        self.api_key = api_key or os.environ.get("KILO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Kilocode API key required. Set KILO_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.base_url = (base_url or os.environ.get("KILO_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
        
        logger.debug("Initialized KilocodeClient with base_url=%s", self.base_url)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
        logger.debug("KilocodeClient closed")
    
    async def list_models(self) -> list[dict[str, Any]]:
        """Fetch all available models from kilocode.
        
        Returns:
            List of model dictionaries containing metadata.
            
        Example:
            >>> models = await client.list_models()
            >>> for model in models:
            ...     print(f"{model['id']}: {model.get('name', 'Unknown')}")
        """
        logger.debug("Fetching models from kilocode...")
        
        response = await self._client.get("/models")
        response.raise_for_status()
        
        data = response.json()
        models = data.get("data", [])
        
        logger.info("Fetched %d models from kilocode", len(models))
        return models
    
    async def list_providers(self) -> list[dict[str, Any]]:
        """Fetch all available providers from kilocode.
        
        Returns:
            List of provider dictionaries.
        """
        logger.debug("Fetching providers from kilocode...")
        
        response = await self._client.get("/providers")
        response.raise_for_status()
        
        data = response.json()
        providers = data.get("data", [])
        
        logger.info("Fetched %d providers from kilocode", len(providers))
        return providers
    
    async def get_model(self, model_id: str) -> dict[str, Any] | None:
        """Get detailed information about a specific model.
        
        Args:
            model_id: The model identifier (e.g., "anthropic/claude-sonnet-4.5").
            
        Returns:
            Model dictionary if found, None otherwise.
        """
        logger.debug("Fetching model details for %s", model_id)
        
        response = await self._client.get(f"/models/{model_id}")
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        return response.json()
