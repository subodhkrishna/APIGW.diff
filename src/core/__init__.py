"""Core abstractions for the testing framework."""

from .gateway_interface import GatewayInterface, GatewayCapability
from .test_case import BaseTestCase, TestResult, TestMetrics, TestStatus

__all__ = [
    "GatewayInterface",
    "GatewayCapability",
    "BaseTestCase",
    "TestResult",
    "TestMetrics",
    "TestStatus",
]
