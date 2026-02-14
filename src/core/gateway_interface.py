"""Abstract base class for API gateway implementations."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp


class GatewayCapability(str, Enum):
    """Enumeration of gateway capabilities."""

    RATE_LIMITING = "rate_limiting"
    AUTHENTICATION = "authentication"
    ROUTING = "routing"
    TRANSFORMATION = "transformation"
    CIRCUIT_BREAKER = "circuit_breaker"
    RETRY = "retry"
    LOAD_BALANCING = "load_balancing"
    CACHING = "caching"
    CORS = "cors"
    TLS_TERMINATION = "tls_termination"
    REQUEST_VALIDATION = "request_validation"
    RESPONSE_VALIDATION = "response_validation"
    LOGGING = "logging"
    METRICS = "metrics"
    TRACING = "tracing"


class GatewayInterface(ABC):
    """Abstract interface that all gateway implementations must follow."""

    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize gateway with name and configuration.

        Args:
            name: Gateway name (e.g., 'kong', 'aws_api_gateway')
            config: Gateway-specific configuration dictionary
        """
        self.name = name
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    @abstractmethod
    async def configure(self) -> None:
        """Configure the gateway with provided settings.

        This method should:
        - Validate configuration
        - Set up authentication
        - Initialize any required resources
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the gateway is healthy and accessible.

        Returns:
            True if gateway is healthy, False otherwise
        """
        pass

    @abstractmethod
    async def send_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: Optional[float] = None,
    ) -> aiohttp.ClientResponse:
        """Send an HTTP request through the gateway.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            headers: Optional request headers
            params: Optional query parameters
            json_data: Optional JSON body
            data: Optional raw request body
            timeout: Optional request timeout in seconds

        Returns:
            aiohttp.ClientResponse object
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[GatewayCapability]:
        """Get list of capabilities supported by this gateway.

        Returns:
            List of GatewayCapability enums
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up gateway resources.

        This method should close connections and release resources.
        """
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        await self.configure()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    def supports_capability(self, capability: GatewayCapability) -> bool:
        """Check if gateway supports a specific capability.

        Args:
            capability: Capability to check

        Returns:
            True if supported, False otherwise
        """
        return capability in self.get_capabilities()

    @property
    def base_url(self) -> str:
        """Get the base URL for the gateway.

        Returns:
            Base URL string
        """
        return self.config.get("url", self.config.get("proxy_url", ""))

    @property
    def is_enabled(self) -> bool:
        """Check if gateway is enabled in configuration.

        Returns:
            True if enabled, False otherwise
        """
        return self.config.get("enabled", True)
