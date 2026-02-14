"""Generic HTTP gateway implementation for testing."""

from typing import Any, Dict, List, Optional

import aiohttp

from ..core.gateway_interface import GatewayCapability, GatewayInterface
from ..utils.logger import get_logger

logger = get_logger(__name__)


class GenericGateway(GatewayInterface):
    """Generic HTTP gateway implementation for simple endpoints."""

    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize generic gateway.

        Args:
            name: Gateway name
            config: Configuration dictionary with:
                - url: Gateway URL
        """
        super().__init__(name, config)
        self.url = config.get("url", "")

    async def configure(self) -> None:
        """Configure generic gateway."""
        logger.info(f"Configuring generic gateway: {self.name}")

        # Create HTTP session
        self._session = aiohttp.ClientSession()

        # Validate configuration
        if not self.url:
            raise ValueError("Generic gateway url is required")

        logger.info(f"Generic gateway configured: {self.url}")

    async def health_check(self) -> bool:
        """Check generic gateway health."""
        try:
            # Try to access the URL
            async with self._session.get(
                f"{self.url}/",
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=False,
            ) as response:
                logger.info(f"Generic gateway health check: status={response.status}")
                return True

        except Exception as e:
            logger.error(f"Generic gateway health check failed: {e}")
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
        """Send request through generic gateway."""
        url = f"{self.url}{path}"

        timeout_obj = aiohttp.ClientTimeout(total=timeout) if timeout else None

        logger.debug(f"Generic gateway request: {method} {url}")

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
        """Get generic gateway capabilities."""
        return [
            GatewayCapability.ROUTING,
            GatewayCapability.TLS_TERMINATION,
            GatewayCapability.LOGGING,
        ]

    async def cleanup(self) -> None:
        """Clean up generic gateway resources."""
        if self._session:
            await self._session.close()
            self._session = None
        logger.info(f"Generic gateway cleanup complete: {self.name}")
