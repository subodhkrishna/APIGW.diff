"""Traefik API Gateway implementation."""

from typing import Any, Dict, List, Optional

import aiohttp

from ..core.gateway_interface import GatewayCapability, GatewayInterface
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TraefikGateway(GatewayInterface):
    """Traefik API Gateway implementation."""

    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize Traefik gateway.

        Args:
            name: Gateway name
            config: Configuration dictionary with:
                - url: Traefik proxy URL
                - api_url: Traefik API URL (optional)
        """
        super().__init__(name, config)
        self.url = config.get("url", "")
        self.api_url = config.get("api_url", "")

    async def configure(self) -> None:
        """Configure Traefik gateway."""
        logger.info(f"Configuring Traefik gateway: {self.name}")

        # Create HTTP session
        self._session = aiohttp.ClientSession()

        # Validate configuration
        if not self.url:
            raise ValueError("Traefik url is required")

        logger.info(f"Traefik gateway configured: {self.url}")

    async def health_check(self) -> bool:
        """Check Traefik gateway health."""
        try:
            # Try to access the API health endpoint if available
            health_url = f"{self.api_url}/ping" if self.api_url else f"{self.url}/"

            async with self._session.get(
                health_url,
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=False,
            ) as response:
                logger.info(f"Traefik health check: status={response.status}")
                return response.status < 500

        except Exception as e:
            logger.error(f"Traefik health check failed: {e}")
            return False

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
        """Send request through Traefik gateway."""
        url = f"{self.url}{path}"

        timeout_obj = aiohttp.ClientTimeout(total=timeout) if timeout else None

        logger.debug(f"Traefik request: {method} {url}")

        response = await self._session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            data=data,
            timeout=timeout_obj,
        )

        return response

    def get_capabilities(self) -> List[GatewayCapability]:
        """Get Traefik capabilities."""
        return [
            GatewayCapability.RATE_LIMITING,
            GatewayCapability.AUTHENTICATION,
            GatewayCapability.ROUTING,
            GatewayCapability.LOAD_BALANCING,
            GatewayCapability.CORS,
            GatewayCapability.TLS_TERMINATION,
            GatewayCapability.LOGGING,
            GatewayCapability.METRICS,
            GatewayCapability.TRACING,
            GatewayCapability.RETRY,
            GatewayCapability.CIRCUIT_BREAKER,
        ]

    async def cleanup(self) -> None:
        """Clean up Traefik gateway resources."""
        if self._session:
            await self._session.close()
            self._session = None
        logger.info(f"Traefik gateway cleanup complete: {self.name}")
