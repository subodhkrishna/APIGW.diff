# Quick Start Guide

Get started with the API Gateway Comparison Testing Framework in 5 minutes.

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure a Gateway

For this quick start, we'll use a public HTTP testing service to demonstrate the framework.

Edit `config/gateways.yaml` and add:

```yaml
gateways:
  httpbin:
    enabled: true
    url: "https://httpbin.org"
```

## 3. Run Your First Test

```bash
python main.py test run --gateway httpbin --test latency
```

You should see output like:

```
Testing gateway: httpbin
✓ Gateway httpbin is healthy
Running test: latency
✓ latency: Completed 100/100 requests. Avg latency: 250.45ms, P95: 450.23ms

Test Summary:
Total: 1
Passed: 1
Failed: 0
Skipped: 0
Errors: 0
```

## 4. Generate an HTML Report

```bash
python main.py test run --gateway httpbin --suite performance --output html
```

Open `reports/results.html` in your browser to see the full report.

## 5. Test Multiple Endpoints

Edit `config/test_suites.yaml` to customize test paths:

```yaml
test_suites:
  performance:
    config:
      path: "/get"
      requests: 50
```

Then run:

```bash
python main.py test run --gateway httpbin --suite performance
```

## Next Steps

### Configure Your Production Gateways

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your gateway URLs and credentials:
   ```bash
   KONG_PROXY_URL=https://your-kong-gateway.com
   KONG_API_KEY=your-api-key
   ```

3. Enable gateways in `config/gateways.yaml`:
   ```yaml
   gateways:
     kong:
       enabled: true
       proxy_url: "${KONG_PROXY_URL}"
       credentials:
         api_key: "${KONG_API_KEY}"
   ```

### Run Tests in Parallel

Test multiple gateways simultaneously:

```bash
python main.py test run --parallel --gateway kong,nginx,traefik
```

### Explore Available Tests

See all available tests:

```bash
python main.py test list
```

See configured gateways:

```bash
python main.py gateway list
```

## Common Use Cases

### Performance Benchmarking

```bash
python main.py test run \
  --gateway aws_api_gateway \
  --suite performance \
  --output html \
  --report-dir ./benchmarks
```

### Feature Comparison

```bash
python main.py test run \
  --parallel \
  --gateway kong,traefik,envoy \
  --suite features \
  --output json
```

### Quick Health Check

```bash
python main.py test run --test routing
```

## Troubleshooting

### "No gateways configured"

Make sure you have at least one gateway enabled in `config/gateways.yaml`.

### Connection errors

1. Verify gateway URLs are accessible: `curl <gateway-url>`
2. Check credentials are correct
3. Use verbose mode: `python main.py test run -v`

### Need help?

- Read the full [README.md](README.md)
- Check configuration examples in `config/`
- Review test implementations in `src/test_suites/`
