"""Base test case classes and result data structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .gateway_interface import GatewayInterface


class TestStatus(str, Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestMetrics:
    """Metrics collected during test execution."""

    # Performance metrics
    duration_seconds: float = 0.0
    avg_latency_ms: Optional[float] = None
    p50_latency_ms: Optional[float] = None
    p95_latency_ms: Optional[float] = None
    p99_latency_ms: Optional[float] = None
    max_latency_ms: Optional[float] = None
    min_latency_ms: Optional[float] = None

    # Throughput metrics
    requests_per_second: Optional[float] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Error metrics
    error_rate: float = 0.0
    errors: List[str] = field(default_factory=list)

    # Custom metrics
    custom: Dict[str, Any] = field(default_factory=dict)

    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100


@dataclass
class TestResult:
    """Result of a test execution."""

    test_name: str
    gateway_name: str
    status: TestStatus
    message: str = ""
    metrics: TestMetrics = field(default_factory=TestMetrics)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def duration_seconds(self) -> float:
        """Calculate test duration in seconds."""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "test_name": self.test_name,
            "gateway_name": self.gateway_name,
            "status": self.status.value,
            "message": self.message,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds(),
            "metrics": {
                "duration_seconds": self.metrics.duration_seconds,
                "avg_latency_ms": self.metrics.avg_latency_ms,
                "p50_latency_ms": self.metrics.p50_latency_ms,
                "p95_latency_ms": self.metrics.p95_latency_ms,
                "p99_latency_ms": self.metrics.p99_latency_ms,
                "max_latency_ms": self.metrics.max_latency_ms,
                "min_latency_ms": self.metrics.min_latency_ms,
                "requests_per_second": self.metrics.requests_per_second,
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "error_rate": self.metrics.error_rate,
                "success_rate": self.metrics.success_rate(),
                "errors": self.metrics.errors,
                "custom": self.metrics.custom,
            },
            "details": self.details,
        }


class BaseTestCase(ABC):
    """Abstract base class for all test cases."""

    def __init__(self, name: str, category: str, config: Optional[Dict[str, Any]] = None):
        """Initialize test case.

        Args:
            name: Test name
            category: Test category (performance, features, reliability, security, configuration)
            config: Optional test-specific configuration
        """
        self.name = name
        self.category = category
        self.config = config or {}
        self.gateway: Optional[GatewayInterface] = None

    @abstractmethod
    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up test prerequisites.

        Args:
            gateway: Gateway interface to test against
        """
        pass

    @abstractmethod
    async def execute(self) -> TestResult:
        """Execute the test.

        Returns:
            TestResult containing test outcome and metrics
        """
        pass

    @abstractmethod
    async def teardown(self) -> None:
        """Clean up test resources."""
        pass

    async def run(self, gateway: GatewayInterface) -> TestResult:
        """Run the complete test lifecycle.

        Args:
            gateway: Gateway to test

        Returns:
            TestResult with test outcome
        """
        result = TestResult(
            test_name=self.name,
            gateway_name=gateway.name,
            status=TestStatus.PENDING,
            start_time=datetime.now(),
        )

        try:
            await self.setup(gateway)
            result = await self.execute()
            result.end_time = datetime.now()

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Test execution failed: {str(e)}"
            result.end_time = datetime.now()
            result.metrics.errors.append(str(e))

        finally:
            try:
                await self.teardown()
            except Exception as e:
                # Don't override test result, but log teardown error
                if result.status != TestStatus.ERROR:
                    result.details["teardown_error"] = str(e)

        return result

    def requires_capability(self, capability: str) -> bool:
        """Check if this test requires a specific capability.

        Args:
            capability: Capability name

        Returns:
            True if capability is required
        """
        required = self.config.get("required_capabilities", [])
        return capability in required

    def should_skip(self, gateway: GatewayInterface) -> tuple[bool, str]:
        """Determine if test should be skipped for this gateway.

        Args:
            gateway: Gateway to check

        Returns:
            Tuple of (should_skip, reason)
        """
        required_caps = self.config.get("required_capabilities", [])
        gateway_caps = [cap.value for cap in gateway.get_capabilities()]

        for cap in required_caps:
            if cap not in gateway_caps:
                return True, f"Gateway does not support required capability: {cap}"

        return False, ""
