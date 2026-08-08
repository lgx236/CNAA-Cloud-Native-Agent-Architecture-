# CNAA Cloud-Local Quick Deploy Guide

## Prerequisites

- ✅ CNAA repository cloned
- ✅ Python 3.10+ installed
- 🎯 Server access (local, VPS, or remote)

---

## Quick Start - Single Machine (Dev Mode)

### 1️⃣ Configure Local Environment

```bash
# Copy template and edit with your settings
cp .env.example .env
nano .env  # Edit the file
```

Update `CNAA_SERVER_URL=http://localhost:8080` for localhost testing.

### 2️⃣ Deploy Cloud Server

```bash
python3 server.py --port 8080
```

Server running at http://localhost:8080 ✅

### 3️⃣ Test Connection

```bash
chmod +x scripts/test_cloud_connection.sh
./scripts/test_cloud_connection.sh
```

Should output: "✅ Connection test successful!" 🎉

---

## Quick Start - Production Deployment (v1.0)

## Deploy Remote - Production Setup

### Step 1: Deploy on Cloud Server (VPS/EC2)

```bash
# Clone on cloud server
git clone https://github.com/your-org/cnaa.git
cd cnaa

# Create production config
cat > .env << 'EOF'
HOST=0.0.0.0
PORT=8080
OPENROUTER_API_KEY=your-key-here
CNAA_AUTH_ENABLED=false
CNAA_DB_PATH=/var/lib/cnaa/memories.db
EOF

# Create database directory
sudo mkdir -p /var/lib/cnaa
sudo chmod 755 /var/lib/cnaa

# Get public IP (replace placeholder in .env later)
PUBLIC_IP=$(curl ifconfig.me)
echo "Your server IP: $PUBLIC_IP"

# Update CNAA_SERVER_URL in .env for clients
sed -i "s/CNAA_SERVER_URL=.*/CNAA_SERVER_URL=http:\/\/$PUBLIC_IP:8080/" .env

# Start server (background mode)
nohup python3 server.py > /var/log/cnaa-server.log 2>&1 &
echo "Cloud server started!"
```

### Step 2: Configure Firewall

**Linux (Ubuntu/Debian):**
```bash
sudo ufw allow 8080/tcp
sudo ufw enable
```

**AWS Security Group:**
- Add inbound rule: Port 8080, CIDR 0.0.0.0/0

**GCP Firewall:**
- Add firewall rule: Allow port 8080 from 0.0.0.0/0

### Step 3: Configure Local Agent Machines

On each local machine (laptop, mobile, etc.):

```bash
# Clone repository
git clone https://github.com/your-org/cnaa.git
cd cnaa

# Configure environment
cat > .env << EOF
CNAA_SERVER_URL=http://CLOUD_SERVER_IP:8080
LOCAL_AGENT_ID=laptop-user1
CNAA_DB_PATH=./local_memories.db
CNAA_STATE_DB_PATH=./local_states.db
EOF

# Replace CLOUD_SERVER_IP with actual value
nano .env
```

### Step 4: Verify Installation

```bash
# Run test script
./scripts/test_cloud_connection.sh

# Check logs
tail -f /var/log/cnaa-server.log
```

---

## Multi-Agent Architecture Diagram

```
┌──────────────────────────────────────┐
│          Cloud Server (Remote)       │
│   ┌────────────────────────────────┐ │
│   │  CNAA MCP Server               │ │
│   │  • Persistent SQLite Storage   │ │
│   │  • API Key Authentication      │ │
│   │  • Data Syncing                │ │
│   └────────────────────────────────┘ │
│              ↓ HTTP                    │
├──────────────────────────────────────┤
│  Agent 1: Laptop                     │
│  • LOCAL_AGENT_ID=laptop-alice       │
│  • ./alice_laptop_memories.db        │
├──────────────────────────────────────┤
│  Agent 2: Mobile                     │
│  • LOCAL_AGENT_ID=mobile-alice       │
│  • ./alice_mobile_memories.db        │
├──────────────────────────────────────┤
│  Agent 3: Desktop                    │
│  • LOCAL_AGENT_ID=desktop-alice      │
│  • ./alice_desktop_memories.db       │
└──────────────────────────────────────┘
All agents sync through same cloud server!
```

---

## Configuration Reference

| Variable | Purpose | Default | Example |
|----------|---------|---------|---------|
| `CNAA_SERVER_URL` | Cloud endpoint | N/A | `http://52.123.456.78:8080` |
| `CNAA_SERVER_API_KEY` | Authentication | Empty | `sk-xxx` |
| `LOCAL_AGENT_ID` | Local identifier | `local-agent-001` | `laptop-alice` |
| `CNAA_DB_PATH` | Memories DB path | `./cnaa_memories.db` | `/var/lib/cnaa/memories.db` |
| `CNAA_STATE_DB_PATH` | States DB path | `./cnaa_states.db` | `/var/lib/cnaa/states.db` |
| `CNAA_LOG_PATH` | Log file location | `./cnaa.log` | `/var/log/cnaa.log` |

See [`docs/CLOUD_LOCAL_DEPLOYMENT.md`](docs/CLOUD_LOCAL_DEPLOYMENT.md) for full guide.

---

## Monitoring & Maintenance

### Check Server Status

```bash
# View active processes
ps aux | grep server.py

# Check recent logs
tail -f /var/log/cnaa-server.log

# View last hour of activity
journalctl -u cnaa-server -n 100
```

### Backup Strategy

```bash
# Create manual backup
mkdir -p backups
tar -czf backups/cnaa-backup-$(date +%Y%m%d).tar.gz \
    *.db ./backups/*.db

# Automatic daily backup (add to crontab)
echo "0 2 * * * cd /path/to/cnaa && bash ./scripts/backup.sh" | crontab -
```

### Troubleshooting

**Cannot connect to server?**

```bash
# Check server is listening
netstat -tlnp | grep 8080
# Or
ss -tlnp | grep 8080

# Test manually from client
curl -v http://CLOUD_SERVER_IP:8080/health
```

**Database errors?**

```bash
# Check permissions
ls -la *.db

# Test read/write
python3 -c "import sqlite3; conn = sqlite3.connect('memories.db'); print(conn.execute('SELECT COUNT(*) FROM memories').fetchone()[0])"
```

---

## Next Steps

1. **Configure AI integration**: Set up OpenRouter API key
2. **Enable authentication**: Generate API keys (`sk-your-api-key`)
3. **Set up monitoring**: Configure log rotation alerts
4. **Schedule backups**: Use `crontab -e` for automated backup
5. **HTTPS setup**: Configure reverse proxy with nginx

See [full deployment documentation](docs/CLOUD_LOCAL_DEPLOYMENT.md) for advanced setups.

---

## Common Issues

| Problem | Solution |
|---------|----------|
| 401 Unauthorized | Verify `CNAA_SERVER_API_KEY` matches cloud config |
| Connection refused | Check firewall rules and server status |
| Database locked | Ensure no other process holding lock |
| Disk space full | Clear old logs or expand storage |

For more help, see [Troubleshooting section](docs/CLOUD_LOCAL_DEPLOYMENT.md#troubleshooting).
