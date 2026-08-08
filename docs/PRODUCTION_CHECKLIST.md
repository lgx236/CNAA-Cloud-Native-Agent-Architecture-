# CNAA v1.0 Production Deployment Checklist

## Pre-Deployment Verification

### ✅ Infrastructure Requirements

- [ ] **Cloud Server Ready**
  - [ ] VPS/EC2 instance running
  - [ ] Port 8080 accessible (firewall configured)
  - [ ] SSL certificate installed (optional, for HTTPS)
  - [ ] Nginx reverse proxy configured (recommended)
  
- [ ] **Database Storage Available**
  - [ ] SQLite files have write permissions (`chmod 644 *.db`)
  - [ ] Sufficient disk space (>500MB recommended)
  - [ ] Backup directory created (`./backups/`)

- [ ] **Environment Variables Configured**
  ```bash
  # At minimum:
  HOST=0.0.0.0
  PORT=8080
  
  # Recommended for production:
  CNAA_AUTH_ENABLED=true
  CNAA_SERVER_URL=http://your-server-ip:8080
  CNAA_API_KEYS='{"sk-prod-key": {"agent_id": "agent-*", "permission": "read_write"}}'
  ```

### ✅ Testing Verification

Run these commands before deployment:

```bash
# 1. Test suite execution
python3 -m pytest tests/ -v --tb=short

# 2. Coverage check (should be ≥ 85% on core modules)
python3 -m pytest --cov=cnaa --cov-report=term-missing -q

# 3. Integration test
./scripts/test_cloud_connection.sh

# 4. Security scan
pip install bandit safety
bandit -r cnaa cloud local
safety check
```

**Expected Results:**
- All unit tests: ✅ PASS
- All integration tests: ✅ PASS  
- Code coverage: ≥ 85%
- No critical security vulnerabilities

### ✅ Performance Baseline

Verify server can handle expected load:

```bash
# Install load testing tool
pip install locust

# Run basic performance check
python3 -c "
import requests
from time import perf_counter

base_url = 'http://localhost:8080'

# Health check latency
start = perf_counter()
requests.get(f'{base_url}/health')
latency = (perf_counter() - start) * 1000
print(f'Health check: {latency:.0f}ms')

assert latency < 100, f'Health check too slow: {latency}ms'
"
```

---

## Deployment Steps

### Step 1: Prepare Cloud Server

**Option A: Direct Deployment**
```bash
# Clone repository
git clone https://github.com/lgx236/CNAA-Cloud-Native-Agent-Architecture-.git
cd CNAA-Cloud-Native-Agent-Architecture-

# Create production environment
cp .env.example .env
nano .env  # Edit with your settings

# Install dependencies
pip install -e ".[dev]"

# Start server
nohup python3 server.py --port 8080 > /var/log/cnaa-server.log 2>&1 &
echo $! > /tmp/cnaa.pid
```

**Option B: Using PM2 (Recommended)**
```bash
# Install PM2 globally
npm install -g pm2

# Configure PM2 ecosystem file
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: "cnaa",
    script: "./server.py",
    args: "--host 0.0.0.0 --port 8080",
    env: {
      NODE_ENV: "production",
      PYTHONUNBUFFERED: "1"
    },
    error_file: "/var/log/cnaa-error.log",
    out_file: "/var/log/cnaa-out.log",
    log_date_format: "YYYY-MM-DD HH:mm:ss"
  }]
}
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Step 2: Verify Server Status

```bash
# Check if server is running
curl -I http://localhost:8080/health
# Expected: HTTP/1.1 200 OK

# Check detailed health
curl http://localhost:8080/health | python3 -m json.tool
# Should show all components as "ok"

# Verify metrics endpoint
curl http://localhost:8080/metrics
# Should return Prometheus format metrics

# Check version info
curl http://localhost:8080/version
# Should show version 1.0.0
```

### Step 3: Set Up Logging

**Configure Log Rotation**
```bash
# Create log directory structure
sudo mkdir -p /var/log/cnaa/{server,access,error}
sudo chmod 755 /var/log/cnaa

# Update server.py to use proper log paths
sed -i 's|cnaa.log|/var/log/cnaa/server.log|g' server.py
```

**Enable Structured Logging**
```bash
# Install structured logging support
pip install structlog

# Verify logs are JSON-formatted
tail -f /var/log/cnaa/server.log | head -5
```

---

## Post-Deployment Monitoring

### Immediate Checks (First Hour)

✅ **Health Check Endpoint**
```bash
# Every 5 minutes for first hour
for i in {1..12}; do
  curl -s http://localhost:8080/health | grep -o '"status":"[^"]*"'
  sleep 5m
done
```

**Expected**: Always shows `"status":"healthy"` or `"status":"degraded"`

✅ **Error Rate Monitoring**
```bash
# Count errors in last hour
grep ERROR /var/log/cnaa/server.log | tail -100
```

**Expected**: Minimal or zero errors after initial startup

✅ **Memory Usage**
```bash
# Monitor memory growth
top -b -n 5 -d 60 | grep python3
```

**Expected**: Stable memory consumption (<200MB)

### Long-Term Monitoring

**Create Alert Rules**

Example Prometheus/Grafana alerts:

```yaml
# Alert when server unhealthy
- alert: CNAAServerUnhealthy
  expr: up{job="cnaa"} == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "CNAA server is down"

# Alert when error rate increases
- alert: CNAAHighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High error rate detected"

# Alert when memory exceeds threshold
- alert: CNAMemoryUsageHigh
  expr: process_resident_memory_bytes{job="cnaa"} > 500000000
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Memory usage above 500MB"
```

---

## Backup Strategy

### Daily Automated Backups

**Backup Script** (already included: `scripts/backup.sh`)
```bash
#!/bin/bash
# Location: ./scripts/backup.sh

set -e
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database files
mkdir -p "$BACKUP_DIR"
for db_file in *.db; do
    if [ -f "$db_file" ]; then
        cp "$db_file" "$BACKUP_DIR/cnaa_${db_file%.*}_${DATE}"
        gzip "$BACKUP_DIR/cnaa_${db_file%.*}_${DATE}"
    fi
done

# Cleanup old backups (keep 7 days)
find "$BACKUP_DIR" -name "*.db.gz" -mtime +7 -delete
```

**Schedule Daily Execution**
```bash
# Add to crontab
crontab -e

# Add this line (runs at 2 AM daily):
0 2 * * * cd /path/to/cnaa && bash ./scripts/backup.sh >> /var/log/cnaa-backup.log 2>&1
```

### Recovery Procedures

**Restore from Backup**
```bash
# Find latest backup
LATEST_BACKUP=$(ls -t ./backups/*.db.gz | head -1)

# Stop server
systemctl stop cnaa  # or pkill -f server.py

# Extract backup
gunzip -c "$LATEST_BACKUP" > cnaa_memories.db

# Restart server
systemctl start cnaa  # or python3 server.py &

# Verify restoration
curl http://localhost:8080/health
```

---

## Security Hardening

### Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS (if using TLS)
sudo ufw allow 8080/tcp # CNAA server
sudo ufw enable
```

### API Key Security

Generate strong API keys:
```bash
# Generate secure random key
openssl rand -hex 32 | sed 's/^/sk-/'

# In .env:
CNAA_API_KEYS='{"sk-$(openssl rand -hex 32)": {"agent_id": "agent-*", "permission": "read_write"}}'
```

### File Permissions

```bash
# Protect sensitive files
chmod 600 .env
chown -R cnaa:cnaa /var/lib/cnaa
chmod 755 /var/lib/cnaa
```

---

## Rollback Procedure

### Emergency Rollback Plan

If issues occur after deployment:

1. **Identify Problem**
   ```bash
   # Check error logs
   tail -f /var/log/cnaa/error.log
   
   # Check health status
   curl http://localhost:8080/health
   ```

2. **Stop Current Version**
   ```bash
   systemctl stop cnaa  # or pm2 stop cnaa
   ```

3. **Downgrade Package**
   ```bash
   pip install cnaa==0.2.0
   ```

4. **Restart Service**
   ```bash
   systemctl start cnaa
   ```

5. **Verify Rollback**
   ```bash
   curl http://localhost:8080/version
   # Should show version 0.2.0
   ```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Server Won't Start
```bash
# Symptoms: Process exits immediately
# Solution:
tail -f /var/log/cnaa/server.log
# Check for Python syntax errors or missing dependencies

pip install -e ".[dev]"  # Ensure all deps installed
```

#### Issue 2: Database Lock Errors
```bash
# Symptoms: "database is locked" messages
# Solution:
sqlite3 cnaa_memories.db "PRAGMA journal_mode=WAL;"
# Enable WAL mode for better concurrency
```

#### Issue 3: High Memory Usage
```bash
# Symptoms: Server consuming >500MB RAM
# Solution:
ps aux | grep python3  # Identify memory-heavy processes
# Implement connection pooling or reduce cache size
```

#### Issue 4: Authentication Failures
```bash
# Symptoms: 401 Unauthorized errors
# Solution:
# Verify API key matches between client and server
grep CNAA_API_KEYS .env
curl -H "Authorization: Bearer sk-your-key" http://localhost:8080/mcp
```

---

## Success Criteria Checklist

### Must Pass Before Going Live ✅

- [ ] Unit tests: 100% passing
- [ ] Integration tests: 100% passing
- [ ] Code coverage: ≥ 85% on core modules
- [ ] Health check endpoint returns 200 OK
- [ ] Metrics endpoint returns valid Prometheus format
- [ ] Error handling tested (invalid inputs rejected)
- [ ] Authentication working (if enabled)
- [ ] Basic load test passed (< 100ms response time)
- [ ] Logs rotating correctly (no single file growing indefinitely)
- [ ] Backup script runs successfully
- [ ] Environment variables documented and secured
- [ ] Rollback procedure tested and verified

### Recommended for Production 🎯

- [ ] Prometheus monitoring dashboard configured
- [ ] Grafana alerting rules active
- [ ] SSL/TLS certificates installed
- [ ] Reverse proxy (nginx/nginx) configured
- [ ] Load balancer set up (if multiple instances)
- [ ] Disaster recovery plan documented
- [ ] On-call rotation established
- [ ] Incident response procedures written
- [ ] User documentation available

### Nice-to-Have Features 🌟

- [ ] Distributed tracing (OpenTelemetry)
- [ ] APM solution (New Relic, Datadog)
- [ ] Custom dashboards
- [ ] Automated scaling policies
- [ ] Multi-region redundancy
- [ ] Blue-green deployment setup

---

## Contact Information

For deployment support or questions:

- **Documentation Issues**: GitHub Issues
- **Production Support**: Use established incident channels
- **Emergency Contacts**: Your organization's on-call rotation

---

*Version: 1.0.0*  
*Last Updated: 2026-08-08*  
*This checklist should be reviewed and updated with each release.*
