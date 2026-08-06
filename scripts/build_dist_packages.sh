#!/bin/bash
# ============================================================================
# CNAA v0.2 - Build Distribution Packages
# Builds separate cloud and local packages for distributed testing
# ============================================================================

set -e

echo "============================================================================"
echo "📦 CNAA v0.2 - Building Distribution Packages"
echo "============================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directories
BUILD_DIR="./dist_packages"
CLOUD_PKG="$BUILD_DIR/cnaa_cloud"
LOCAL_PKG="$BUILD_DIR/cnaa_local"

# Clean previous builds
cleanup() {
    echo -e "${YELLOW}Cleaning previous builds...${NC}"
    rm -rf "$BUILD_DIR"
    rm -rf dist/ *.egg-info/ 2>/dev/null || true
    mkdir -p "$BUILD_DIR"
}

# Build Cloud Package
build_cloud() {
    echo -e "\n${BLUE}🌩️  Building cnaa-cloud package...${NC}"
    echo "-------------------------------------------------------------"
    
    cp pyproject.cloud.toml cloud_pyproject.toml
    
    python3 -m pip install --quiet --break-system-packages build twine
    
    PYTHONPATH="/root/CNAA-Cloud-Native-Agent-Architecture-$PYTHONPATH" \
        python3 -m build --outdir "$CLOUD_PKG" --config-file cloud_pyproject.toml
    
    rm -f cloud_pyproject.toml
    
    # List built files
    echo ""
    echo -e "${GREEN}✅ Built Cloud Package Contents:${NC}"
    ls -lh "$CLOUD_PKG"/*.whl "$CLOUD_PKG"/*.tar.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    
    # Calculate checksums
    echo ""
    echo -e "${YELLOW}🔐 Checksums:${NC}"
    sha256sum "$CLOUD_PKG"/*.whl 2>/dev/null | while read checksum filename; do
        echo "  $checksum  $(basename $filename)"
    done
}

# Build Local Package
build_local() {
    echo -e "\n${BLUE}💻 Building cnaa-local package...${NC}"
    echo "-------------------------------------------------------------"
    
    cp pyproject.local.toml local_pyproject.toml
    
    python3 -m pip install --quiet --break-system-packages build twine
    
    PYTHONPATH="/root/CNAA-Cloud-Native-Agent-Architecture-$PYTHONPATH" \
        python3 -m build --outdir "$LOCAL_PKG" --config-file local_pyproject.toml
    
    rm -f local_pyproject.toml
    
    # List built files
    echo ""
    echo -e "${GREEN}✅ Built Local Package Contents:${NC}"
    ls -lh "$LOCAL_PKG"/*.whl "$LOCAL_PKG"/*.tar.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    
    # Calculate checksums
    echo ""
    echo -e "${YELLOW}🔐 Checksums:${NC}"
    sha256sum "$LOCAL_PKG"/*.whl 2>/dev/null | while read checksum filename; do
        echo "  $checksum  $(basename $filename)"
    done
}

# Create installation guides
create_guides() {
    echo -e "\n${BLUE}📚 Creating installation guides...${NC}"
    echo "-------------------------------------------------------------"
    
    cat > "$BUILD_DIR/install_cloud.md" << 'EOF'
# CNAA Cloud Server Installation Guide

## Quick Install

```bash
pip install ./cnaa_cloud/cnaa_cloud-*-py3-none-any.whl
```

## From Source

```bash
pip install ./cnaa_cloud/cnaa_cloud-*-tar.tar.gz
```

## Verify Installation

```bash
# Check package
pip show cnaa-cloud

# Test server
cnaa-server --help
```

## Dependencies

Core dependencies (auto-installed):
- requests>=2.31.0
- mcp>=1.0.0

Optional:
- SQLite (built-in, no install needed)

## Usage Example

```python
from cloud.storage import CNAAStorageBackend

storage = CNAAStorageBackend(
    storage_type="sqlite",
    path="./cnaa_memories.db"
)

# Store memory
memory = {
    "agent_id": "test-agent",
    "content": {"task": "Demo"},
    "timestamp": datetime.now().isoformat()
}
storage.store_memory(memory)
```

## Documentation

See full documentation:
https://github.com/lgx236/CNAA-Cloud-Native-Agent-Architecture-/blob/main/README.md
EOF

    cat > "$BUILD_DIR/install_local.md" << 'EOF'
# CNAA Local Client Installation Guide

## Quick Install

```bash
pip install ./cnaa_local/cnaa_local-*-py3-none-any.whl
```

## From Source

```bash
pip install ./cnaa_local/cnaa_local-*-tar.tar.gz
```

## Verify Installation

```bash
# Check package
pip show cnaa-local

# Test client
python -c "from local.client import CNAA_MCPClient; print('✅ OK')"
```

## Dependencies

Core dependencies (auto-installed):
- requests>=2.31.0
- mcp>=1.0.0

Framework Adapters (optional):
- langchain>=0.1.0        # For LangChain integration
- llama-index>=0.10.0     # For LlamaIndex integration
- pyautogen>=0.2.0        # For AutoGen integration
- crewai>=0.1.0           # For CrewAI integration

Install specific frameworks:
```bash
pip install ./cnaa_local/cnaa_local[-framework-adapters]
```

## Usage Examples

### Basic HTTP Client

```python
from local.client import CNAA_MCPClient

client = CNAA_MCPClient(
    server_url="http://localhost:8080",
    timeout=30.0
)

# Store memory
result = client.store_memory(
    agent_id="my-agent",
    memory_id="task-001",
    type="long_term",
    content={"description": "Test memory"},
    completion_score=1.0
)
```

### With LangChain Adapter

```python
from langchain.agents import AgentExecutor
from cnaa.adapters.langchain import LangChainCNAAMixin

class MyAgent(LangChainCNAAMixin, AgentExecutor):
    agent_id = "my-langchain-agent"
    
    def _call(self, inputs):
        result = super()._call(inputs)
        self.on_task_complete(self.agent_id, result)
        return result
```

### Multi-Language Support

TypeScript clients available in examples:
examples/cnaa_client/typescript/cnaa_client.ts

## Documentation

See full documentation:
https://github.com/lgx236/CNAA-Cloud-Native-Agent-Architecture-/blob/main/README.md
EOF

    echo -e "${GREEN}✅ Created installation guides:${NC}"
    echo "  - $BUILD_DIR/install_cloud.md"
    echo "  - $BUILD_DIR/install_local.md"
}

# Display summary
display_summary() {
    echo ""
    echo "============================================================================"
    echo "📦 BUILD SUMMARY"
    echo "============================================================================"
    echo ""
    
    echo -e "${GREEN}🌩️  Cloud Package:${NC}"
    echo "  Location: $CLOUD_PKG/"
    echo "  Files:"
    find "$CLOUD_PKG" -type f -name "*.whl" -o -name "*.tar.gz" 2>/dev/null | while read file; do
        size=$(ls -lh "$file" | awk '{print $5}')
        name=$(basename "$file")
        echo "    • $name ($size)"
    done
    
    echo ""
    echo -e "${GREEN}💻 Local Package:${NC}"
    echo "  Location: $LOCAL_PKG/"
    echo "  Files:"
    find "$LOCAL_PKG" -type f -name "*.whl" -o -name "*.tar.gz" 2>/dev/null | while read file; do
        size=$(ls -lh "$file" | awk '{print $5}')
        name=$(basename "$file")
        echo "    • $name ($size)"
    done
    
    echo ""
    echo -e "${GREEN}📚 Guides:${NC}"
    echo "  - $BUILD_DIR/install_cloud.md"
    echo "  - $BUILD_DIR/install_local.md"
    
    echo ""
    echo "============================================================================"
    echo "🚀 NEXT STEPS"
    echo "============================================================================"
    echo ""
    echo "To test distributed system:"
    echo ""
    echo "1️⃣ Deploy Cloud Server (Machine A):"
    echo "   pip install $CLOUD_PKG/*.whl"
    echo "   cnaa-server --host 0.0.0.0 --port 8080"
    echo ""
    echo "2️⃣ Install Client on Local Machine (Machine B):"
    echo "   pip install $LOCAL_PKG/*.whl"
    echo ""
    echo "3️⃣ Run Distributed Tests:"
    echo "   cd /root/CNAA-Cloud-Native-Agent-Architecture-"
    echo "   python tests/test_distributed_system.py"
    echo ""
    echo "============================================================================"
    echo "✨ BUILD COMPLETE!"
    echo "============================================================================"
}

# Main execution
main() {
    cleanup
    build_cloud
    build_local
    create_guides
    display_summary
    
    echo -e "\n${GREEN}Packages ready for GitHub release!${NC}\n"
}

main "$@"
