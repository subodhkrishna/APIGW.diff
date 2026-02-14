"""NGINX API Gateway implementation."""

from typing import Any, Dict, List, Optional

import aiohttp

from ..core.gateway_interface import GatewayCapability, GatewayInterface
from ..utils.logger import get_logger

logger = get_logger(__name__)


class NGINXGateway(GatewayInterface):
    """NGINX API Gateway implementation."""

    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize NGINX gateway.

        Args:
            name: Gateway name
            config: Configuration dictionary with:
                - url: NGINX proxy URL
                - api_url: NGINX Plus API URL (optional)
        """
        super().__init__(name, config)
        self.url = config.get("url", "")
        self.api_url = config.get("api_url", "")

    async def configure(self) -> None:
        """Configure NGINX gateway."""
        logger.info(f"Configuring NGINX gateway: {self.name}")

        # Create HTTP session
        self._session = aiohttp.ClientSession()

        # Validate configuration
        if not self.url:
            raise ValueError("NGINX url is required")

        logger.info(f"NGINX gateway configured: {self.url}")

    async def health_check(self) -> bool:
        """Check NGINX gateway health."""
        try:
            # Try to access the proxy URL
            async with self._session.get(
                f"{self.url}/",
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=False,
            ) as response:
                logger.info(f"NGINX health check: status={response.status}")
                return True

        except Exception as e:
            logger.error(f"NGINX health check failed: {e}")
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
        """Send request through NGINX gateway."""
        url = f"{self.url}{path}"

        timeout_obj = aiohttp.ClientTimeout(total=timeout) if timeout else None

        logger.debug(f"NGINX request: {method} {url}")

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
        """Get NGINX capabilities."""
        return [
            GatewayCapability.RATE_LIMITING,
            GatewayCapability.AUTHENTICATION,
            GatewayCapability.ROUTING,
            GatewayCapability.LOAD_BALANCING,
            GatewayCapability.CACHING,
            GatewayCapability.CORS,
            GatewayCapability.TLS_TERMINATION,
            GatewayCapability.LOGGING,
            GatewayCapability.RETRY,
        ]

    async def cleanup(self) -> None:
        """Clean up NGINX gateway resources."""
        if self._session:
            await self._session.close()
            self._session = None
        logger.info(f"NGINX gateway cleanup complete: {self.name}")
