# Docker Compose Local Testing

This Docker Compose setup provides local gateway instances for testing the framework without requiring cloud resources.

## Services

- **httpbin** (port 8080) - HTTP testing service
- **nginx** (port 8081) - NGINX gateway
- **traefik** (port 8082, dashboard 8083) - Traefik gateway
- **kong** (port 8000 proxy, 8001 admin) - Kong gateway with PostgreSQL

## Quick Start

### Start All Gateways

```bash
cd deployment/docker
docker-compose up -d
```

### Verify Gateways Are Running

```bash
# Check all services
docker-compose ps

# Test individual gateways
curl http://localhost:8080/get              # httpbin
curl http://localhost:8081/                 # nginx
curl http://localhost:8082/                 # traefik
curl http://localhost:8000/                 # kong
curl http://localhost:8001/                 # kong admin
```

### Configure Framework for Local Testing

Update `config/gateways.yaml`:

```yaml
gateways:
  local_httpbin:
    enabled: true
    url: "http://localhost:8080"

  local_nginx:
    enabled: true
    url: "http://localhost:8081"

  local_traefik:
    enabled: true
    url: "http://localhost:8082"
    api_url: "http://localhost:8083"

  local_kong:
    enabled: true
    proxy_url: "http://localhost:8000"
    admin_url: "http://localhost:8001"
```

### Run Tests

```bash
# Return to project root
cd ../..

# Run tests against local gateways
python main.py test run --gateway local_kong,local_nginx,local_traefik

# Or test all local gateways in parallel
python main.py test run --parallel
```

## Individual Gateway Management

### Start Specific Gateway

```bash
docker-compose up -d nginx
docker-compose up -d kong kong-database
```

### Stop All Gateways

```bash
docker-compose down
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f kong
```

### Restart Gateway

```bash
docker-compose restart nginx
```

## Kong Setup

Kong requires initial database migration. This is handled automatically by the `kong-migration` service, but if you need to reset:

```bash
# Stop Kong
docker-compose stop kong kong-migration

# Reset database
docker-compose down kong-database
docker volume prune

# Start fresh
docker-compose up -d kong-database
docker-compose up kong-migration
docker-compose up -d kong
```

## Traefik Dashboard

Access Traefik dashboard at: http://localhost:8083

## Troubleshooting

### Port Conflicts

If ports are already in use, modify `docker-compose.yaml` to use different ports:

```yaml
ports:
  - "9080:80"  # Use 9080 instead of 8080
```

### Gateway Not Responding

1. Check if service is running: `docker-compose ps`
2. Check logs: `docker-compose logs <service>`
3. Restart service: `docker-compose restart <service>`

### Clean Reset

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Start fresh
docker-compose up -d
```

## Advanced Configuration

### Custom NGINX Configuration

Create `nginx.conf` in this directory with your custom configuration.

### Kong Plugins

Configure Kong plugins via Admin API:

```bash
# Add rate limiting
curl -X POST http://localhost:8001/plugins \
  --data "name=rate-limiting" \
  --data "config.minute=100"

# Add authentication
curl -X POST http://localhost:8001/plugins \
  --data "name=key-auth"
```

Then test with the framework:

```bash
python main.py test run --gateway local_kong --test rate_limiting
```

## Resource Requirements

Minimum:
- CPU: 2 cores
- RAM: 4GB
- Disk: 2GB

Recommended:
- CPU: 4 cores
- RAM: 8GB
- Disk: 5GB

## Network

All services are on the `gateway-test` network. Services can communicate with each other using service names:

- `http://httpbin/`
- `http://nginx/`
- `http://traefik/`
- `http://kong:8000/`
