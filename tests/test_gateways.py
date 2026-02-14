"""Unit tests for gateway implementations."""

import pytest
from src.gateways import get_gateway_class, GATEWAY_REGISTRY
from src.core.gateway_interface import GatewayCapability


def test_gateway_registry():
    """Test that all gateways are registered."""
    expected_gateways = ["kong", "aws_api_gateway", "nginx", "traefik", "envoy"]
    for gateway_name in expected_gateways:
        assert gateway_name in GATEWAY_REGISTRY


def test_get_gateway_class():
    """Test getting gateway class by name."""
    gateway_class = get_gateway_class("kong")
    assert gateway_class is not None


def test_get_invalid_gateway():
    """Test getting invalid gateway raises error."""
    with pytest.raises(ValueError):
        get_gateway_class("invalid_gateway")


def test_gateway_initialization():
    """Test gateway initialization."""
    gateway_class = get_gateway_class("kong")
    config = {"url": "http://test.example.com", "enabled": True}
    gateway = gateway_class("test_kong", config)

    assert gateway.name == "test_kong"
    assert gateway.config == config
    assert gateway.is_enabled


def test_gateway_capabilities():
    """Test that gateways report capabilities."""
    for gateway_name in GATEWAY_REGISTRY:
        gateway_class = get_gateway_class(gateway_name)
        config = {"url": "http://test.example.com"}
        gateway = gateway_class(gateway_name, config)

        capabilities = gateway.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
        assert all(isinstance(cap, GatewayCapability) for cap in capabilities)


def test_gateway_capability_check():
    """Test checking if gateway supports capability."""
    gateway_class = get_gateway_class("kong")
    config = {"url": "http://test.example.com"}
    gateway = gateway_class("kong", config)

    assert gateway.supports_capability(GatewayCapability.ROUTING)
