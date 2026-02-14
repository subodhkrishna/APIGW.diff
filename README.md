# API Gateway Comparison Testing Framework

A comprehensive, extensible Python-based framework for comparing the capabilities, performance, and features of multiple API gateway solutions including Kong, AWS API Gateway, NGINX, Traefik, and Envoy.

## Features

- **Multi-Gateway Support**: Test Kong, AWS API Gateway, NGINX, Traefik, and Envoy
- **Comprehensive Test Coverage**:
  - **Performance**: Latency, throughput, load testing
  - **Features**: Rate limiting, authentication, routing, transformations
  - **Reliability**: Error handling, retries, circuit breakers
  - **Security**: TLS, authentication, CORS
  - **Configuration**: Setup complexity, API flexibility
- **Parallel Execution**: Test multiple gateways simultaneously
- **Multiple Output Formats**: Console, JSON, and HTML reports
- **Cloud-Ready**: Designed for testing cloud-deployed gateways
- **Extensible**: Easy to add new gateways and test cases

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd api-gateway-comparison
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your gateways:
```bash
cp .env.example .env
# Edit .env with your gateway URLs and credentials
```

4. Enable gateways in configuration:
```bash
# Edit config/gateways.yaml to enable/configure your gateways
```

## Quick Start

### List Available Tests

```bash
python main.py test list
```

### List Configured Gateways

```bash
python main.py gateway list
```

### Run All Tests on All Enabled Gateways

```bash
python main.py test run
```

### Test Specific Gateway

```bash
python main.py test run --gateway kong
```

### Test Multiple Gateways in Parallel

```bash
python main.py test run --parallel --gateway kong,traefik,envoy
```

### Run Specific Test Suite

```bash
python main.py test run --suite performance
```

### Run Specific Test

```bash
python main.py test run --test latency
```

### Generate HTML Report

```bash
python main.py test run --output html --report-dir ./reports
```

### Generate JSON Report

```bash
python main.py test run --output json --report-dir ./reports
```

### Dry Run (See What Would Be Tested)

```bash
python main.py test run --dry-run
```

## Configuration

### Gateway Configuration

Edit `config/gateways.yaml` to configure your gateways:

```yaml
gateways:
  kong:
    enabled: true
    proxy_url: "https://kong.example.com"
    admin_url: "https://kong-admin.example.com"
    credentials:
      api_key: "${KONG_API_KEY}"

  aws_api_gateway:
    enabled: true
    url: "https://api-id.execute-api.us-east-1.amazonaws.com/prod"
    region: "us-east-1"
    credentials:
      api_key: "${AWS_API_KEY}"
```

### Test Suite Configuration

Edit `config/test_suites.yaml` to configure test suites:

```yaml
test_suites:
  performance:
    enabled: true
    tests:
      - latency
      - throughput
      - load
    config:
      requests: 100
      duration: 30
      concurrent: 10
```

### Environment Variables

Use `.env` file or environment variables for sensitive data:

```bash
KONG_PROXY_URL=https://kong.example.com
KONG_API_KEY=your-api-key
AWS_API_GATEWAY_URL=https://your-api-gateway.com
```

## Project Structure

```
api-gateway-comparison/
├── config/                    # Configuration files
│   ├── gateways.yaml         # Gateway configurations
│   ├── test_suites.yaml      # Test suite definitions
│   └── credentials.yaml.example
├── src/
│   ├── core/                 # Core abstractions
│   │   ├── gateway_interface.py
│   │   └── test_case.py
│   ├── gateways/            # Gateway implementations
│   │   ├── kong.py
│   │   ├── aws_api_gateway.py
│   │   ├── nginx.py
│   │   ├── traefik.py
│   │   └── envoy.py
│   ├── test_suites/         # Test implementations
│   │   ├── performance/
│   │   ├── features/
│   │   ├── reliability/
│   │   ├── security/
│   │   └── configuration/
│   ├── runners/             # Test execution
│   │   ├── test_runner.py
│   │   └── parallel_executor.py
│   ├── reporters/           # Report generation
│   │   ├── console_reporter.py
│   │   ├── json_reporter.py
│   │   └── html_reporter.py
│   └── utils/               # Utilities
├── reports/                 # Generated reports
├── main.py                  # CLI entry point
└── requirements.txt
```

## Extending the Framework

### Adding a New Gateway

1. Create a new file in `src/gateways/`:

```python
# src/gateways/my_gateway.py
from ..core.gateway_interface import GatewayInterface, GatewayCapability

class MyGateway(GatewayInterface):
    async def configure(self) -> None:
        # Setup logic
        pass

    async def health_check(self) -> bool:
        # Health check logic
        pass

    async def send_request(self, method, path, **kwargs):
        # Request logic
        pass

    def get_capabilities(self):
        return [GatewayCapability.ROUTING, ...]

    async def cleanup(self) -> None:
        # Cleanup logic
        pass
```

2. Register in `src/gateways/__init__.py`:

```python
from .my_gateway import MyGateway

GATEWAY_REGISTRY = {
    # ...
    "my_gateway": MyGateway,
}
```

3. Add configuration to `config/gateways.yaml`:

```yaml
gateways:
  my_gateway:
    enabled: true
    url: "https://my-gateway.example.com"
```

### Adding a New Test

1. Create a new test file in the appropriate suite directory:

```python
# src/test_suites/performance/my_test.py
from ...core.test_case import BaseTestCase, TestResult, TestStatus

class MyTest(BaseTestCase):
    def __init__(self, config=None):
        super().__init__("my_test", "performance", config)

    async def setup(self, gateway):
        self.gateway = gateway

    async def execute(self):
        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )
        # Test logic here
        result.status = TestStatus.PASSED
        result.message = "Test completed"
        return result

    async def teardown(self):
        pass
```

2. Register in `src/runners/test_runner.py`:

```python
TEST_REGISTRY = {
    # ...
    "my_test": MyTest,
}
```

3. Add to test suite in `config/test_suites.yaml`:

```yaml
test_suites:
  performance:
    tests:
      - my_test
```

## Test Categories

### Performance Tests
- **Latency**: Measure request latency with percentile breakdowns (P50, P95, P99)
- **Throughput**: Test concurrent request handling capacity
- **Load**: Gradual ramp-up load testing

### Feature Tests
- **Rate Limiting**: Validate rate limiting enforcement
- **Authentication**: Test authentication mechanisms
- **Routing**: Verify routing capabilities
- **Transformation**: Test request/response transformations

### Reliability Tests
- **Error Handling**: Test error response handling
- **Retry**: Validate retry mechanisms
- **Circuit Breaker**: Test circuit breaker functionality

### Security Tests
- **TLS**: Verify TLS/SSL configuration
- **CORS**: Test CORS policy enforcement
- **Auth**: Authentication security testing

### Configuration Tests
- **Setup Complexity**: Assess configuration complexity
- **API Flexibility**: Evaluate API flexibility

## Reports

### Console Output
Rich formatted console output with tables and status indicators.

### JSON Report
Machine-readable JSON with complete test results:
```json
{
  "generated_at": "2024-01-01T00:00:00",
  "summary": { ... },
  "results": [ ... ],
  "results_by_gateway": { ... }
}
```

### HTML Report
Interactive HTML report with:
- Summary dashboard
- Results by gateway
- Performance comparison tables
- Sortable and filterable results

## CLI Reference

### Test Commands

```bash
# Run tests
python main.py test run [OPTIONS]

Options:
  -g, --gateway TEXT     Specific gateway(s) to test
  -s, --suite TEXT       Specific test suite(s) to run
  -t, --test TEXT        Specific test(s) to run
  -p, --parallel         Run in parallel
  -o, --output [console|json|html]  Output format
  --report-dir PATH      Report directory
  --dry-run              Dry run mode
  -v, --verbose          Verbose output

# List available tests
python main.py test list

# List configured gateways
python main.py gateway list
```

## Examples

### Test Production API Gateway Performance

```bash
python main.py test run \
  --gateway aws_api_gateway \
  --suite performance \
  --output html \
  --report-dir ./reports/production
```

### Compare Multiple Gateways in Parallel

```bash
python main.py test run \
  --parallel \
  --gateway kong,nginx,traefik \
  --output json \
  --report-dir ./reports/comparison
```

### Quick Health Check

```bash
python main.py test run \
  --test routing \
  --gateway all
```

## Troubleshooting

### Gateway Connection Issues

1. Verify gateway URLs in `config/gateways.yaml`
2. Check environment variables are set correctly
3. Test gateway health manually: `curl <gateway-url>`
4. Enable verbose logging: `python main.py test run -v`

### Configuration Errors

1. Validate YAML syntax: `python -m yaml config/gateways.yaml`
2. Check environment variable references
3. Ensure required fields are present

### Test Failures

1. Check test-specific configuration in `test_suites.yaml`
2. Verify gateway supports required capabilities
3. Review test logs with verbose mode: `-v`

## License

[Your License Here]

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]
