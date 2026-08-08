# CNAA Docker Configuration

## Quick Start

### Build Image
```bash
docker build -t cnaa-server .
```

### Run Container
```bash
docker run -d \
  --name cnaa \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  cnaa-server
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host address | `0.0.0.0` |
| `PORT` | Server port | `8080` |
| `STORAGE_TYPE` | Storage backend type | `sqlite` |
| `DB_PATH` | Database file path | `/app/data/cnaa_data.db` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CNAA_AUTH_ENABLED` | Enable authentication | `false` |
| `CNAA_API_KEYS` | API key configuration | `{}` |

## Volume Mounts

Mount volumes for persistent data:
- `/app/data` - SQLite database files and logs

Example:
```bash
-v $(pwd)/data:/app/data
```

## Health Check

Container includes automatic health check:
- Runs every 30 seconds
- Timeout: 5 seconds
- Retries: 3

Check container health:
```bash
docker inspect --format='{{.State.Health.Status}}' cnaa
```

## Logs

View container logs:
```bash
docker logs -f cnaa
```

## Stop & Remove

```bash
docker stop cnaa
docker rm cnaa
```
