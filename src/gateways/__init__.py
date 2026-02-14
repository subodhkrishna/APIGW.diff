"""Gateway implementations."""

from typing import Dict, Type

from ..core.gateway_interface import GatewayInterface
from .aws_api_gateway import AWSAPIGateway
from .envoy import EnvoyGateway
from .kong import KongGateway
from .nginx import NGINXGateway
from .traefik import TraefikGateway
from .generic import GenericGateway

# Gateway registry for dynamic instantiation
GATEWAY_REGISTRY: Dict[str, Type[GatewayInterface]] = {
    "kong": KongGateway,
    "aws_api_gateway": AWSAPIGateway,
    "nginx": NGINXGateway,
    "traefik": TraefikGateway,
    "envoy": EnvoyGateway,
    "httpbin": GenericGateway,
    "generic": GenericGateway,
}


def get_gateway_class(gateway_name: str) -> Type[GatewayInterface]:
    """Get gateway class by name.

    Args:
        gateway_name: Name of the gateway

    Returns:
        Gateway class

    Raises:
        ValueError: If gateway not found
    """
    if gateway_name not in GATEWAY_REGISTRY:
        raise ValueError(
            f"Unknown gateway: {gateway_name}. "
            f"Available: {', '.join(GATEWAY_REGISTRY.keys())}"
        )
    return GATEWAY_REGISTRY[gateway_name]


__all__ = [
    "KongGateway",
    "AWSAPIGateway",
    "NGINXGateway",
    "TraefikGateway",
    "EnvoyGateway",
    "GenericGateway",
    "GATEWAY_REGISTRY",
    "get_gateway_class",
]
