# Testing Guide

This document provides guidance for testing the API Gateway Comparison Framework itself.

## Running Unit Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_gateways.py

# Run with verbose output
pytest -v
```

## Manual Testing

### 1. Test Gateway Configuration Loading

```bash
python3 -c "
from src.utils.config_loader import ConfigLoader
loader = ConfigLoader()
gateways = loader.load_gateways_config()
print('Gateways configured:', list(gateways.get('gateways', {}).keys()))
"
```

### 2. Test Gateway Class Loading

```bash
python3 -c "
from src.gateways import GATEWAY_REGISTRY
print('Available gateways:', list(GATEWAY_REGISTRY.keys()))
"
```

### 3. Test CLI Help

```bash
python main.py --help
python main.py test --help
python main.py gateway --help
```

### 4. Test with Public HTTP Service

To test without setting up real gateways, use httpbin.org:

1. Add to `config/gateways.yaml`:
```yaml
gateways:
  httpbin:
    enabled: true
    url: "https://httpbin.org"
```

2. Run tests:
```bash
python main.py test run --gateway httpbin --test latency
```

### 5. Dry Run Test

```bash
python main.py test run --dry-run
```

## Integration Testing

### Test with Local Mock Gateway

Create a simple mock gateway server:

```python
# mock_gateway.py
from aiohttp import web

async def handle_request(request):
    return web.Response(text="OK", status=200)

app = web.Application()
app.router.add_route('*', '/{path:.*}', handle_request)

if __name__ == '__main__':
    web.run_app(app, port=8080)
```

Configure it in `config/gateways.yaml`:
```yaml
gateways:
  local_mock:
    enabled: true
    url: "http://localhost:8080"
```

Run tests:
```bash
python mock_gateway.py &
python main.py test run --gateway local_mock
```

## Verification Checklist

### Core Framework
- [ ] Gateway registry contains all 5 gateways
- [ ] Test registry contains all tests
- [ ] Config loader reads YAML files
- [ ] Config loader interpolates environment variables
- [ ] Logger initializes correctly

### Gateways
- [ ] Each gateway can be instantiated
- [ ] Each gateway reports capabilities
- [ ] Each gateway implements all required methods
- [ ] Health checks work (when gateway is available)

### Test Cases
- [ ] Each test can be instantiated
- [ ] Each test reports correct category
- [ ] Tests handle missing capabilities gracefully
- [ ] Tests produce valid TestResult objects

### Test Runner
- [ ] Can run single test
- [ ] Can run test suite
- [ ] Can filter by gateway
- [ ] Can run in parallel mode
- [ ] Generates correct summary

### Reporters
- [ ] Console reporter produces formatted output
- [ ] JSON reporter creates valid JSON
- [ ] HTML reporter creates valid HTML
- [ ] Reports are saved to correct directory

### CLI
- [ ] Help commands work
- [ ] Test list command works
- [ ] Gateway list command works
- [ ] Test run command works with all options
- [ ] Error messages are clear

## Performance Testing

Test the framework's own performance:

```bash
# Time a test run
time python main.py test run --gateway httpbin --suite performance

# Test parallel execution
time python main.py test run --parallel --gateway httpbin,httpbin2,httpbin3
```

## Troubleshooting Tests

### Import Errors

Ensure you're in the correct directory and virtual environment:
```bash
pwd  # Should be in api-gateway-comparison/
which python  # Should point to venv/bin/python
```

### Configuration Errors

Validate YAML syntax:
```bash
python3 -c "import yaml; yaml.safe_load(open('config/gateways.yaml'))"
```

### Test Failures

Run with verbose logging:
```bash
python main.py test run -v
```

Check test logs for details.

## Adding New Tests

When adding new tests, verify:

1. **Test Registration**: Test appears in `python main.py test list`
2. **Test Execution**: Test runs without errors
3. **Test Results**: Test produces valid TestResult
4. **Test Cleanup**: No resources leaked after test
5. **Test Documentation**: Docstrings are clear

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=src
      - name: Test CLI
        run: |
          python main.py test list
          python main.py gateway list
```
