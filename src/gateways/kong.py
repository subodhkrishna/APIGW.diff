"""Kong API Gateway implementation."""

from typing import Any, Dict, List, Optional

import aiohttp

from ..core.gateway_interface import GatewayCapability, GatewayInterface
from ..utils.logger import get_logger

logger = get_logger(__name__)


class KongGateway(GatewayInterface):
    """Kong API Gateway implementation."""

    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize Kong gateway.

        Args:
            name: Gateway name
            config: Configuration dictionary with:
                - proxy_url: Kong proxy URL
                - admin_url: Kong admin API URL (optional)
                - credentials: Optional API key/token
        """
        super().__init__(name, config)
        self.proxy_url = config.get("proxy_url", config.get("url", ""))
        self.admin_url = config.get("admin_url", "")
        self.api_key = config.get("credentials", {}).get("api_key", "")

    async def configure(self) -> None:
        """Configure Kong gateway."""
        logger.info(f"Configuring Kong gateway: {self.name}")

        # Create HTTP session
        headers = {}
        if self.api_key:
            headers["apikey"] = self.api_key

        self._session = aiohttp.ClientSession(headers=headers)

        # Validate configuration
        if not self.proxy_url:
            raise ValueError("Kong proxy_url is required")

        logger.info(f"Kong gateway configured: {self.proxy_url}")

    async def health_check(self) -> bool:
        """Check Kong gateway health."""
        try:
            # Try to access the proxy URL with a simple request
            async with self._session.get(
                f"{self.proxy_url}/",
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=False,
            ) as response:
                # Any response from Kong (even 404) means it's up
                logger.info(f"Kong health check: status={response.status}")
                return True

        except Exception as e:
            logger.error(f"Kong health check failed: {e}")
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
        """Send request through Kong gateway."""
        url = f"{self.proxy_url}{path}"

        # Merge headers
        request_headers = dict(self._session.headers)
        if headers:
            request_headers.update(headers)

        timeout_obj = aiohttp.ClientTimeout(total=timeout) if timeout else None

        logger.debug(f"Kong request: {method} {url}")

        response = await self._session.request(
            method=method,
            url=url,
            headers=request_headers,
            params=params,
            json=json_data,
            data=data,
            timeout=timeout_obj,
        )

        return response

    def get_capabilities(self) -> List[GatewayCapability]:
        """Get Kong capabilities."""
        return [
            GatewayCapability.RATE_LIMITING,
            GatewayCapability.AUTHENTICATION,
            GatewayCapability.ROUTING,
            GatewayCapability.TRANSFORMATION,
            GatewayCapability.LOAD_BALANCING,
            GatewayCapability.CACHING,
            GatewayCapability.CORS,
            GatewayCapability.TLS_TERMINATION,
            GatewayCapability.LOGGING,
            GatewayCapability.METRICS,
            GatewayCapability.RETRY,
            GatewayCapability.CIRCUIT_BREAKER,
        ]

    async def cleanup(self) -> None:
        """Clean up Kong gateway resources."""
        if self._session:
            await self._session.close()
            self._session = None
        logger.info(f"Kong gateway cleanup complete: {self.name}")
