"""Envoy Proxy API Gateway implementation."""

from typing import Any, Dict, List, Optional

import aiohttp

from ..core.gateway_interface import GatewayCapability, GatewayInterface
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EnvoyGateway(GatewayInterface):
    """Envoy Proxy API Gateway implementation."""

    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize Envoy gateway.

        Args:
            name: Gateway name
            config: Configuration dictionary with:
                - url: Envoy proxy URL
                - admin_url: Envoy admin API URL (optional)
        """
        super().__init__(name, config)
        self.url = config.get("url", "")
        self.admin_url = config.get("admin_url", "")

    async def configure(self) -> None:
        """Configure Envoy gateway."""
        logger.info(f"Configuring Envoy gateway: {self.name}")

        # Create HTTP session
        self._session = aiohttp.ClientSession()

        # Validate configuration
        if not self.url:
            raise ValueError("Envoy url is required")

        logger.info(f"Envoy gateway configured: {self.url}")

    async def health_check(self) -> bool:
        """Check Envoy gateway health."""
        try:
            # Try admin health endpoint if available, otherwise proxy root
            health_url = f"{self.admin_url}/ready" if self.admin_url else f"{self.url}/"

            async with self._session.get(
                health_url,
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=False,
            ) as response:
                logger.info(f"Envoy health check: status={response.status}")
                return response.status < 500

        except Exception as e:
            logger.error(f"Envoy health check failed: {e}")
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
        """Send request through Envoy gateway."""
        url = f"{self.url}{path}"

        timeout_obj = aiohttp.ClientTimeout(total=timeout) if timeout else None

        logger.debug(f"Envoy request: {method} {url}")

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
        """Get Envoy capabilities."""
        return [
            GatewayCapability.RATE_LIMITING,
            GatewayCapability.AUTHENTICATION,
            GatewayCapability.ROUTING,
            GatewayCapability.LOAD_BALANCING,
            GatewayCapability.TLS_TERMINATION,
            GatewayCapability.LOGGING,
            GatewayCapability.METRICS,
            GatewayCapability.TRACING,
            GatewayCapability.RETRY,
            GatewayCapability.CIRCUIT_BREAKER,
            GatewayCapability.CORS,
        ]

    async def cleanup(self) -> None:
        """Clean up Envoy gateway resources."""
        if self._session:
            await self._session.close()
            self._session = None
        logger.info(f"Envoy gateway cleanup complete: {self.name}")
