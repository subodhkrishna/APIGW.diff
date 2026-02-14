"""Unit tests for test runners."""

import pytest
from src.runners.test_runner import TEST_REGISTRY


def test_test_registry():
    """Test that tests are registered."""
    assert len(TEST_REGISTRY) > 0
    assert "latency" in TEST_REGISTRY
    assert "throughput" in TEST_REGISTRY


def test_test_initialization():
    """Test test case initialization."""
    latency_test_class = TEST_REGISTRY["latency"]
    test = latency_test_class({"requests": 50})

    assert test.name == "latency"
    assert test.category == "performance"
    assert test.config["requests"] == 50
