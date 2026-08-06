# CNAA v0.2 - Dual Package Distribution Guide

> **Version**: 0.2.0 | **Date**: 2026-08-06  
> **Purpose**: Complete guide to Cloud and Local package distribution for distributed testing

---

## 📦 Overview: Why Two Packages?

CNAA is now distributed as **two separate packages** to enable true **distributed deployment**:

### 1️⃣ `cnaa-cloud` (Cloud Server Side)
- Contains: `cloud/`, `cnaa/` modules
- Purpose: Run MCP Server, manage storage
- Deploy on: Cloud server machine
- Access: Via HTTP API (`POST /mcp`)

### 2️⃣ `cnaa-local` (Local Client Side)  
- Contains: `local/`, `cnaa/` modules
- Purpose: HTTP client, adapters for agent frameworks
- Deploy on: Agent machine(s)
- Access: Call cloud server via network

This separation allows:
- ✅ Independent deployment of cloud and agents
- ✅ Different dependency management
- ✅ True distributed system testing
- ✅ Flexible scaling

---

## 🚀 Build Instructions

### Option A: Using Automated Script (Recommended)

```bash
cd /root/CNAA-Cloud-Native-Agent-Architecture-

# Build both packages
chmod +x scripts/build_dist_packages.sh
./scripts/build_dist_packages.sh
```

Output location:
```
dist_packages/
├── cnaa_cloud/
│   ├── cnaa_cloud-0.2.0-py3-none-any.whl    # Wheel package
│   └── cnaa_cloud-0.2.0.tar.gz             # Source tarball
├── cnaa_local/
│   ├── cnaa_local-0.2.0-py3-none-any.whl    # Wheel package
│   └── cnaa_local-0.2.0.tar.gz             # Source tarball
└── install_guides/
    ├── install_cloud.md
    └── install_local.md
```

### Option B: Manual Build Commands

```bash
# Install build tools
python3 -m pip install --break-system-packages build twine

# Build Cloud package
PYTHONPATH="/root/CNAA-Cloud-Native-Agent-Architecture-$PYTHONPATH" \
  python3 -m build --outdir dist_packages/cnaa_cloud \
  --config-file pyproject.cloud.toml

# Build Local package  
PYTHONPATH="/root/CNAA-Cloud-Native-Agent-Architecture-$PYTHONPATH" \
  python3 -m build --outdir dist_packages/cnaa_local \
  --config-file pyproject.local.toml

# Verify checksums
sha256sum dist_packages/cnaa_cloud/*.whl
sha256sum dist_packages/cnaa_local/*.whl
```

---

## 📋 Installation Guides

### Install Cloud Package

On **Machine A** (Cloud Server):

```bash
# Install from wheel (fastest)
pip install ./dist_packages/cnaa_cloud/cnaa_cloud-0.2.0-py3-none-any.whl

# OR from source
pip install ./dist_packages/cnaa_cloud/cnaa_cloud-0.2.0.tar.gz

# Verify installation
pip show cnaa-cloud
cnaa-server --help
```

**Dependencies installed automatically**:
- `requests>=2.31.0`
- `mcp>=1.0.0`

### Install Local Package

On **Machine B** (Agent Machine):

```bash
# Install from wheel
pip install ./dist_packages/cnaa_local/cnaa_local-0.2.0-py3-none-any.whl

# OR install with framework adapters
pip install ./dist_packages/cnaa_local[cnaa_local-0.2.0-py3-none-any.whl] \
  "[framework-adapters]"

# Verify installation
pip show cnaa-local
python -c "from local.client import CNAA_MCPClient; print('✅ OK')"
```

**Dependencies installed automatically**:
- `requests>=2.31.0`
- `mcp>=1.0.0`

**Optional framework adapters**:
```bash
pip install ./dist_packages/cnaa_local/[extra=framework-adapters]
```

Install specific frameworks:
```bash
# LangChain support
pip install langchain
# Then use: from cnaa.adapters.langchain import LangChainCNAAMixin

# LlamaIndex support
pip install llama-index
# Then use: from cnaa.adapters.llamaindex import LlamaIndexCNAAMixin

# AutoGen support
pip install pyautogen
# Then use: from cnaa.adapters.autogen import AutoGencNAAAMixin

# CrewAI support
pip install crewai
# Then use: from cnaa.adapters.crewai import CrewAICNAAAMixin
```

---

## 🧪 Testing Distributed System

### Setup Environment

**Machine A** (Cloud Server - IP: 192.168.1.100):
```bash
# Start CNAA Cloud Server
cnaa-server --host 0.0.0.0 --port 8080 &

# Check server status
curl http://localhost:8080/health
# Should return: {"status": "healthy"}

# Keep server running (optional screen/tmux)
screen -S cnaa_server
cnaa-server --host 0.0.0.0 --port 8080
# Ctrl+A then D to detach
```

**Machine B** (Agent Machine - any network-accessible host):
```bash
# Install local client
pip install ./dist_packages/cnaa_local/cnaa_local-0.2.0-py3-none-any.whl

# Test connectivity
python << 'EOF'
from local.client import CNAA_MCPClient

client = CNAA_MCPClient(
    server_url="http://192.168.1.100:8080",
    timeout=30.0
)

# Test health check
if client.health_check():
    print("✅ Connected to Cloud Server!")
    
    # Test store memory
    result = client.store_memory(
        agent_id="test-agent",
        memory_id="mem-001",
        type="long_term",
        content={"task": "Test distributed memory"},
        completion_score=1.0
    )
    print(f"Memory stored: {result}")
else:
    print("❌ Cannot connect to cloud server")
EOF
```

### Run Full Distributed Tests

```bash
cd /root/CNAA-Cloud-Native-Agent-Architecture-

# Comprehensive distributed system tests
python tests/test_distributed_system.py

# Real environment integration test
python tests/test_real_openclaw_integration.py

# End-to-end workflow test
python tests/test_e2e_full_loop.py
```

---

## 🔍 Package Contents Verification

### Verify Cloud Package

```bash
# Extract and inspect
unzip -l dist_packages/cnaa_cloud/cnaa_cloud-0.2.0-py3-none-any.whl

# Key files included:
# ✅ cloud/server/mcp_server.py      (HTTP Server implementation)
# ✅ cloud/storage/*.py              (Storage backends)
# ✅ cloud/agent.py                  (Cloud agent interface)
# ✅ cnaa/models.py                  (Data models)
# ✅ cnaa/tools.py                   (MCP tools definition)
# ✅ cnaa/security.py               (Authentication)
```

### Verify Local Package

```bash
# Extract and inspect
unzip -l dist_packages/cnaa_local/cnaa_local-0.2.0-py3-none-any.whl

# Key files included:
# ✅ local/client/mcp_client_real.py   (HTTP client)
# ✅ local/memory/instant_memory.py    (Local memory)
# ✅ local/state/state_cache.py        (State cache)
# ✅ local/agent.py                    (Local agent interface)
# ✅ cnaa/adapters/*                   (Framework adapters)
# ✅ cnaa/models.py                    (Shared data models)
```

---

## 📊 Expected Behavior in Distributed Mode

### Scenario: Multi-Agent Collaboration

**Setup**:
- Machine A: Cloud server at `192.168.1.100:8080`
- Machine B: LangChain agent calling cloud server
- Machine C: TypeScript agent calling same cloud server

**Flow**:
```
[Machine B] LangChain Agent
    ↓ POST /mcp {"tool":"cnaa_store_memory", ...}
[Machine A] CNAA Cloud Server
    ↓ Store in SQLite database
    └─ cnaa_memories.db

[Machine C] TypeScript Agent (Node.js)
    ↓ GET /mcp {"tool":"cnaa_list_memories", ...}
[Machine A] CNAA Cloud Server
    ↓ Retrieve shared memories
    └─ Returns memories from both agents!
```

**Result**: Both agents share memories despite running on different machines and using different programming languages!

---

## 🛡️ Security Considerations

### For Production Deployment

#### Enable API Key Authentication

Edit `.env`:
```ini
API_KEY_ENABLED=true
API_KEYS=your-secret-key-1,your-secret-key-2
```

Server will require:
```bash
Authorization: Bearer your-secret-key-1
```

#### Network Security

Use firewall rules:
```bash
# Allow only specific IPs to access cloud server
ufw allow from 192.168.1.0/24 to any port 8080
ufw deny 8080
```

Or use HTTPS with reverse proxy:
```nginx
server {
    listen 443 ssl;
    server_name cnaa.your-domain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # SSL configuration
        ssl_certificate /path/to/cert.pem;
        ssl_certificate_key /path/to/key.pem;
    }
}
```

---

## 🐛 Troubleshooting

### Connection Issues

**Problem**: Client cannot connect to cloud server

**Solution**:
1. Check server is running: `systemctl status cnaa-server`
2. Verify firewall: `ufw status | grep 8080`
3. Test connectivity: `telnet <server-ip> 8080`
4. Check logs: `tail -f logs/cnaa.log`

### Dependency Conflicts

**Problem**: Import errors after installation

**Solution**:
```bash
# Reinstall with force upgrade
pip install --force-reinstall --no-deps \
  ./dist_packages/cnaa_cloud/cnaa_cloud-0.2.0-py3-none-any.whl
```

### Cross-Origin Resource Sharing (CORS)

**Problem**: Browser-based clients fail with CORS error

**Solution**: Add headers to server in `cloud/server/mcp_server.py`:
```python
def handle_preflight(self):
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    self.end_headers()
```

---

## 🎯 Verification Checklist

Before marking release as ready:

- [ ] Both packages build successfully without errors
- [ ] Cloud package installs cleanly on fresh Ubuntu 24.04 VM
- [ ] Local package installs with optional dependencies
- [ ] Cloud server starts and responds to health checks
- [ ] Client can connect to server across network
- [ ] Memory persistence works after server restart
- [ ] Distributed tests pass (>90% success rate)
- [ ] Security validation completes (no credential leaks)

---

## 📞 Support Resources

**Documentation**:
- Main README: https://github.com/lgx236/CNAA-Cloud-Native-Agent-Architecture-/blob/main/README.md
- Integration Guide: docs/AGENT_INTEGRATION_GUIDE.md
- Technical Implementation: docs/technical-implementation.md

**Testing Tools**:
- Acceptance Test Script: `scripts/acceptance_test.sh`
- Distributed Test Suite: `tests/test_distributed_system.py`
- Performance Benchmark: `tests/test_large_scale_performance.py`

**Issue Reporting**:
- GitHub Issues: https://github.com/lgx236/CNAA-Cloud-Native-Agent-Architecture-/issues
- Include package versions: `pip freeze | grep cnaa`

---

## ✨ Summary

CNAA v0.2 now offers:

✅ **Dual Package Architecture** - Separate cloud and local components  
✅ **True Distributed Deployment** - Independent deployment on multiple machines  
✅ **Cross-Language Support** - Python, TypeScript, Go, Java all work together  
✅ **Flexible Dependencies** - Minimal core + optional adapters  
✅ **Production Ready** - Security, logging, error handling built-in  

**Ready for:**
- Development testing
- Integration verification  
- Production deployment

**Next Steps**:
1. Build packages using script above
2. Deploy to test environments
3. Run distributed tests
4. Validate security controls
5. Prepare for production release

---

**Last Updated**: 2026-08-06  
**Maintained By**: CNAA Development Team
