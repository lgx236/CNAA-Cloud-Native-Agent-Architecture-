# CNAA Cloud-Local Architecture Deployment Guide

## Overview

CNAA uses a **distributed client-server architecture**:
- **Cloud Server** (Remote): Runs on cloud server, handles persistent storage
- **Local Agent** (Local): Runs on agent machine, provides MCP client interface

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloud Server (Remote)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          CNAA MCP Server (port 8080)                   │ │
│  │   ┌──────────────┐    ┌──────────────┐                │ │
│  │   │ SQLite Store │    │ State Store  │                │ │
│  │   │(memories.db) │    │ (states.db)  │                │ │
│  │   └──────────────┘    └──────────────┘                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                         ↑ HTTP/MCP
                         │ 
              CNAA_SERVER_URL=http://cloud-ip:8080
                         │
┌─────────────────────────────────────────────────────────────┐
│                 Local Machine (Agent)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          Local MCP Client                              │ │
│  │   • Connects to cloud server                          │ │
│  │   • Stores local cache                                │ │
│  │   • Manages instant memory                            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Variables Setup

### Production Setup (`/path/to/cnaa/.env`)

```bash
# =============================================================================
# CNAA Cloud-Local Architecture Configuration
# =============================================================================

# -----------------------------------------------------------------------------
# Cloud Server Endpoint Configuration
# -----------------------------------------------------------------------------

# Set this to your cloud server address (where CNAA server runs)
# Format: http://<server-ip>:<port> or https://<domain>:<port>
CNAA_SERVER_URL=http://your-cloud-server-ip:8080

# Alternative formats:
# - Public domain: https://cnaa.example.com
# - Internal IP: http://192.168.1.100:8080
# - Localhost dev: http://localhost:8080

# -----------------------------------------------------------------------------
# Cloud Server Authentication (Optional)
# -----------------------------------------------------------------------------

# API key for accessing cloud server
# Generate with: python3 -c "import secrets; print('sk-' + secrets.token_hex(16))"
CNAA_SERVER_API_KEY=sk-your-api-key-here

# If authentication is disabled, leave empty or set placeholder
# CNAA_SERVER_API_KEY=

# -----------------------------------------------------------------------------
# Local Agent Identification
# -----------------------------------------------------------------------------

# Unique identifier for this local agent instance
# Used to distinguish between multiple agents connecting to same cloud
LOCAL_AGENT_ID=local-agent-001

# Example multi-device setup:
# LOCAL_AGENT_ID=alice-laptop
# LOCAL_AGENT_ID=alice-mobile
# LOCAL_AGENT_ID=alice-desktop

# -----------------------------------------------------------------------------
# Persistent Storage Configuration  
# -----------------------------------------------------------------------------

# SQLite database paths for local caching
# Stored locally on agent machine for fast access
CNAA_DB_PATH=./cnaa_memories.db
CNAA_STATE_DB_PATH=./cnaa_states.db

# Absolute path recommended for production:
# CNAA_DB_PATH=/var/lib/cnaa-client/memories.db
# CNAA_STATE_DB_PATH=/var/lib/cnaa-client/states.db

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------

# Log file location
CNAA_LOG_PATH=./cnaa.log

# Recommended absolute path:
# CNAA_LOG_PATH=/var/log/cnaa-client/cnaa.log

# -----------------------------------------------------------------------------
# Cloud Server Security Settings (If auth enabled)
# -----------------------------------------------------------------------------

# Optional: Additional security settings
CNAA_AUTH_ENABLED=false
CNAA_ALLOW_UNAUTHENTICATED=true

# API keys mapping on cloud server (set on server, not client)
CNAA_API_KEYS={}"

# -----------------------------------------------------------------------------
# Development vs Production Environments
# -----------------------------------------------------------------------------

# Development (.env.dev):
# CNAA_SERVER_URL=http://localhost:8080
# CNAA_SERVER_API_KEY=
# CNAA_DB_PATH=./dev_memories.db
# CNAA_STATE_DB_PATH=./dev_states.db

# Production (.env.prod):
# CNAA_SERVER_URL=https://cnaa.your-company.com
# CNAA_SERVER_API_KEY=sk-prod-key-xxx
# CNAA_DB_PATH=/var/lib/cnaa/memories.db
# CNAA_STATE_DB_PATH=/var/lib/cnaa/states.db
```

---

## Deployment Scenarios

### Scenario 1: Single Local Agent (Simple Dev Setup)

```bash
# .env configuration
cat > .env << EOF
CNAA_SERVER_URL=http://localhost:8080
CNAA_SERVER_API_KEY=
CNAA_DB_PATH=./memories.db
CNAA_STATE_DB_PATH=./states.db
EOF

# Start cloud server (on same machine)
python server.py --port 8080 &

# Run agent/applications (will connect to localhost:8080)
python my_agent_app.py
```

---

### Scenario 2: Remote Cloud Server + Local Agents

#### Step 1: Deploy Cloud Server

On cloud server (e.g., VPS, AWS EC2):

```bash
# Create deployment directory
sudo mkdir -p /opt/cnaa-cloud
cd /opt/cnaa-cloud

# Copy codebase here (git clone or copy files)

# Create environment file
cat > .env << 'EOF'
HOST=0.0.0.0
PORT=8080
CNAA_AUTH_ENABLED=true
CNAA_API_KEYS='{"sk-cloud-key": {"agent_id": "agent-*", "permission": "read_write"}}'
CNAA_DB_PATH=/var/lib/cnaa/cloud_memories.db
CNAA_STATE_DB_PATH=/var/lib/cnaa/cloud_states.db
EOF

# Start server in background
nohup python3 server.py > /var/log/cnaa-cloud.log 2>&1 &

# Firewall config (open port 8080)
sudo ufw allow 8080/tcp

echo "✅ Cloud server running at http://YOUR_SERVER_IP:8080"
```

**Get your server's public IP:**
```bash
# On Linux/Mac:
curl ifconfig.me

# Or check network settings
hostname -I  # Shows all IP addresses
```

---

#### Step 2: Configure Local Agent

On local agent machine (laptop, mobile, etc.):

```bash
# Clone repository
git clone https://github.com/your-org/cnaa.git
cd cnaa

# Create environment file with cloud server config
cat > .env << 'EOF'
# Replace with your actual cloud server IP
CNAA_SERVER_URL=http://52.123.456.78:8080
CNAA_SERVER_API_KEY=sk-cloud-key
CNAA_DB_PATH=./local_memories.db
CNAA_STATE_DB_PATH=./local_states.db
EOF

# Update .gitignore to exclude sensitive configs
git add .gitignore
git commit -m "Add production configs to gitignore"
```

---

### Scenario 3: Multi-Agent Sharing Same Cloud

Multiple agents (laptop, phone, desktop) sharing one cloud server:

```bash
# Laptop configuration (.env)
cat > .env << 'EOF'
CNAA_SERVER_URL=http://cloud-server-ip:8080
CNAA_SERVER_API_KEY=sk-shared-key
LOCAL_AGENT_ID=laptop-alice
CNAA_DB_PATH=./alice_laptop_memories.db
EOF

# Phone configuration (.env)
cat > .env << 'EOF'
CNAA_SERVER_URL=http://cloud-server-ip:8080
CNAA_SERVER_API_KEY=sk-shared-key
LOCAL_AGENT_ID=mobile-alice
CNAA_DB_PATH=./alice_mobile_memories.db
EOF

# Desktop configuration (.env)
cat > .env << 'EOF'
CNAA_SERVER_URL=http://cloud-server-ip:8080
CNAA_SERVER_API_KEY=sk-shared-key
LOCAL_AGENT_ID=desktop-alice
CNAA_DB_PATH=./alice_desktop_memories.db
EOF

# All three instances will sync through the same cloud server!
```

---

## Testing the Connection

### Test Script: `test_cloud_connection.py`

```python
#!/usr/bin/env python3
"""Test cloud server connectivity."""

import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

# Load env
from dotenv import load_dotenv
load_dotenv()

print("🔍 Testing CNAA Cloud Connection\n")

# Get configuration
server_url = os.getenv("CNAA_SERVER_URL")
api_key = os.getenv("CNAA_SERVER_API_KEY")

if not server_url:
    print("❌ CNAA_SERVER_URL not configured!")
    sys.exit(1)

print(f"✅ Configured Cloud URL: {server_url}")

# Try health check
import urllib.request
try:
    response = urllib.request.urlopen(f"{server_url}/health", timeout=5)
    if response.status == 200:
        print("✅ Cloud server is reachable!")
        data = response.read().decode()
        print(f"   Response: {data[:100]}...")
    else:
        print(f"⚠️ Unexpected status: {response.status}")
except Exception as e:
    print(f"❌ Cannot connect to cloud server!")
    print(f"   Error: {e}")
    print("\n🔧 Troubleshooting:")
    print("   1. Verify CNAA_SERVER_URL is correct")
    print("   2. Check firewall allows outbound connections")
    print("   3. Ensure cloud server is running")
    sys.exit(1)

if api_key:
    print(f"\n✅ API Key configured")
else:
    print(f"\n⚠️ No API Key - authentication disabled on client")
    print("   Make sure cloud server allows unauthenticated requests")

print("\n✅ Connection test successful!")
```

Usage:
```bash
chmod +x test_cloud_connection.py
python3 test_cloud_connection.py
```

---

## Security Best Practices

### For Cloud Servers

1. **Enable HTTPS** (recommended):
```bash
# Use nginx reverse proxy with SSL
nginx -t && systemctl restart nginx
# Access via: https://your-domain.com instead of HTTP
```

2. **Use strong API keys**:
```bash
# Generate secure random key
openssl rand -hex 32
# Output example: sk-a1b2c3d4e5f6...
```

3. **Configure firewall rules**:
```bash
# Only allow necessary IPs
sudo ufw allow from YOUR_AGENCY_IP to any port 8080
sudo ufw enable
```

### For Local Agents

1. **Never commit `.env` files**:
```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.db" >> .gitignore
echo "cnaa.log" >> .gitignore
git commit .gitignore
```

2. **Use relative paths** for databases when possible
3. **Encrypt sensitive keys** if sharing codebase

---

## Monitoring & Maintenance

### Check Cloud Server Logs

```bash
tail -f /var/log/cnaa-cloud.log
journalctl -u cnaa-server -f
```

### Monitor Active Connections

```bash
# List connected agents
ps aux | grep server.py
# Look for active connections

# Check database size
du -sh *.db
```

### Backup Strategy

```bash
# Backup cloud databases daily
crontab -e
# Add:
0 2 * * * cd /opt/cnaa-cloud && ./scripts/backup.sh
```

---

## Troubleshooting

### Issue: Cannot Connect to Cloud Server

**Symptoms**:
- Request timeouts
- Connection refused errors

**Solutions**:
1. Verify `CNAA_SERVER_URL` is accessible
2. Check firewall rules on cloud server
3. Ensure server is running on expected port
4. Test manually: `curl http://cloud-ip:8080/health`

### Issue: Authentication Failures

**Symptoms**:
- 401 Unauthorized errors
- Permission denied

**Solutions**:
1. Verify `CNAA_SERVER_API_KEY` matches cloud configuration
2. Check that API key exists in cloud server's `CNAA_API_KEYS`
3. Ensure permission levels match required operations

### Issue: Database Errors

**Symptoms**:
- Permission denied on DB files
- Disk space issues

**Solutions**:
1. Check file permissions: `ls -la *.db`
2. Ensure write access: `chmod 666 memories.db`
3. Monitor disk space: `df -h`
4. Consider using system directories: `/var/lib/cnaa/`

---

## Quick Reference

| Variable | Purpose | Example Value |
|----------|---------|---------------|
| `CNAA_SERVER_URL` | Cloud server endpoint | `http://52.123.456.78:8080` |
| `CNAA_SERVER_API_KEY` | Authentication token | `sk-xxx` |
| `LOCAL_AGENT_ID` | Local agent identifier | `laptop-alice` |
| `CNAA_DB_PATH` | Local memories DB | `./memories.db` |
| `CNAA_STATE_DB_PATH` | Local states DB | `./states.db` |
| `CNAA_LOG_PATH` | Log file location | `./cnaa.log` |

**Important Notes**:
- 📝 Never commit `.env` files with secrets
- 🔒 Always use HTTPS in production
- 🔄 Keep cloud and local configs synchronized
- 📊 Monitor disk usage for database growth
