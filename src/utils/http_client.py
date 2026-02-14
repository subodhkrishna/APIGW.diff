"""Async HTTP client with retry logic and metrics collection."""

import asyncio
import time
from typing import Any, Dict, Optional

import aiohttp


class AsyncHTTPClient:
    """Async HTTP client wrapper with built-in retry and metrics."""

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize HTTP client.

        Args:
            base_url: Base URL for requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Create session on context entry."""
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session on context exit."""
        if self._session:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: Optional[float] = None,
        retry: bool = True,
    ) -> tuple[aiohttp.ClientResponse, float]:
        """Send HTTP request with retry logic and latency measurement.

        Args:
            method: HTTP method
            path: Request path
            headers: Request headers
            params: Query parameters
            json_data: JSON body
            data: Raw body data
            timeout: Override timeout
            retry: Enable retry logic

        Returns:
            Tuple of (response, latency_ms)
        """
        url = f"{self.base_url}{path}" if self.base_url else path
        custom_timeout = aiohttp.ClientTimeout(total=timeout) if timeout else self.timeout

        attempt = 0
        last_exception = None

        while attempt <= (self.max_retries if retry else 0):
            try:
                start_time = time.perf_counter()

                async with self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    data=data,
                    timeout=custom_timeout,
                ) as response:
                    # Read response to calculate full latency
                    await response.read()
                    latency_ms = (time.perf_counter() - start_time) * 1000

                    # Return response (note: body is already read)
                    return response, latency_ms

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                attempt += 1

                if attempt <= self.max_retries and retry:
                    await asyncio.sleep(self.retry_delay * attempt)
                else:
                    raise

        # Should not reach here, but for type safety
        raise last_exception or Exception("Request failed")

    async def get(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, float]:
        """Send GET request."""
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, float]:
        """Send POST request."""
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, float]:
        """Send PUT request."""
        return await self.request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, float]:
        """Send DELETE request."""
        return await self.request("DELETE", path, **kwargs)

    async def close(self):
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
