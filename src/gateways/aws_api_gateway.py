"""AWS API Gateway implementation."""

from typing import Any, Dict, List, Optional

import aiohttp

from ..core.gateway_interface import GatewayCapability, GatewayInterface
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AWSAPIGateway(GatewayInterface):
    """AWS API Gateway implementation."""

    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize AWS API Gateway.

        Args:
            name: Gateway name
            config: Configuration dictionary with:
                - url: API Gateway invoke URL
                - region: AWS region
                - api_id: API Gateway ID (optional)
                - stage: Stage name (optional)
                - credentials: AWS credentials (optional, uses default chain if not provided)
        """
        super().__init__(name, config)
        self.url = config.get("url", "")
        self.region = config.get("region", "us-east-1")
        self.api_id = config.get("api_id", "")
        self.stage = config.get("stage", "prod")
        self.credentials = config.get("credentials", {})

    async def configure(self) -> None:
        """Configure AWS API Gateway."""
        logger.info(f"Configuring AWS API Gateway: {self.name}")

        # Create HTTP session
        headers = {
            "Content-Type": "application/json",
        }

        # Add API key if provided
        api_key = self.credentials.get("api_key")
        if api_key:
            headers["x-api-key"] = api_key

        self._session = aiohttp.ClientSession(headers=headers)

        # Validate configuration
        if not self.url:
            # Construct URL from api_id and region if not provided
            if self.api_id and self.region:
                self.url = (
                    f"https://{self.api_id}.execute-api.{self.region}.amazonaws.com/{self.stage}"
                )
            else:
                raise ValueError("AWS API Gateway url or (api_id + region) is required")

        logger.info(f"AWS API Gateway configured: {self.url}")

    async def health_check(self) -> bool:
        """Check AWS API Gateway health."""
        try:
            # Try to access a common health endpoint or root
            async with self._session.get(
                f"{self.url}/",
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=False,
            ) as response:
                # AWS API Gateway returns various codes, any response means it's up
                logger.info(f"AWS API Gateway health check: status={response.status}")
                return response.status < 500

        except Exception as e:
            logger.error(f"AWS API Gateway health check failed: {e}")
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
        """Send request through AWS API Gateway."""
        url = f"{self.url}{path}"

        # Merge headers
        request_headers = dict(self._session.headers)
        if headers:
            request_headers.update(headers)

        timeout_obj = aiohttp.ClientTimeout(total=timeout) if timeout else None

        logger.debug(f"AWS API Gateway request: {method} {url}")

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
        """Get AWS API Gateway capabilities."""
        return [
            GatewayCapability.RATE_LIMITING,
            GatewayCapability.AUTHENTICATION,
            GatewayCapability.ROUTING,
            GatewayCapability.TRANSFORMATION,
            GatewayCapability.CORS,
            GatewayCapability.TLS_TERMINATION,
            GatewayCapability.REQUEST_VALIDATION,
            GatewayCapability.RESPONSE_VALIDATION,
            GatewayCapability.LOGGING,
            GatewayCapability.METRICS,
            GatewayCapability.CACHING,
        ]

    async def cleanup(self) -> None:
        """Clean up AWS API Gateway resources."""
        if self._session:
            await self._session.close()
            self._session = None
        logger.info(f"AWS API Gateway cleanup complete: {self.name}")
