#!/bin/bash
# ============================================================================
# CNAA v0.2 - Simple Manual Package Builder
# Creates zip distributions for quick testing
# ============================================================================

set -e

echo "============================================================================"
echo "📦 CNAA v0.2 - Creating Quick Test Packages"
echo "============================================================================"
echo ""

BUILD_DIR="./dist_packages"
mkdir -p "$BUILD_DIR/cnaa_cloud" "$BUILD_DIR/cnaa_local"

echo -e "${YELLOW}Creating Cloud Package Structure...${NC}"
echo "-------------------------------------------------------------"

# Cloud package contents
cp -r cloud "$BUILD_DIR/cnaa_cloud/"
cp -r cnaa "$BUILD_DIR/cnaa_cloud/"
cp server.py mcp_stdio_server.py scripts/start.sh "$BUILD_DIR/cnaa_cloud/"
cp .env.example "$BUILD_DIR/cnaa_cloud/"

# Add requirements file
cat > "$BUILD_DIR/cnaa_cloud/requirements.txt" << 'EOF'
requests>=2.31.0
mcp>=1.0.0
EOF

echo "✅ Cloud package structure ready"
echo "  Location: $BUILD_DIR/cnaa_cloud/"

echo ""
echo -e "${YELLOW}Creating Local Package Structure...${NC}"
echo "-------------------------------------------------------------"

# Local package contents  
cp -r local "$BUILD_DIR/cnaa_local/"
cp -r cnaa "$BUILD_DIR/cnaa_local/"
cp examples/show_integration_patterns.py examples/multi_agent_framework_demo.py "$BUILD_DIR/cnaa_local/"

# Add requirements file
cat > "$BUILD_DIR/cnaa_local/requirements.txt" << 'EOF'
requests>=2.31.0
mcp>=1.0.0

# Optional framework adapters (install as needed)
# langchain>=0.1.0
# llama-index>=0.10.0
# pyautogen>=0.2.0
# crewai>=0.1.0
EOF

echo "✅ Local package structure ready"
echo "  Location: $BUILD_DIR/cnaa_local/"

echo ""
echo "============================================================================"
echo "📋 PACKAGE SUMMARY"
echo "============================================================================"
echo ""

echo -e "${GREEN}🌩️  Cloud Package:${NC}"
ls -la "$BUILD_DIR/cnaa_cloud/" | head -5
echo "  Size: $(du -sh "$BUILD_DIR/cnaa_cloud/" | awk '{print $1}')"
echo ""

echo -e "${GREEN}💻 Local Package:${NC}"  
ls -la "$BUILD_DIR/cnaa_local/" | head -5
echo "  Size: $(du -sh "$BUILD_DIR/cnaa_local/" | awk '{print $1}')"

echo ""
echo "============================================================================"
echo "🚀 QUICK TEST INSTRUCTIONS"
echo "============================================================================"
echo ""
echo "To test distributed deployment:"
echo ""
echo "1️⃣ Deploy Cloud Server (Machine A):"
echo "   cd $BUILD_DIR/cnaa_cloud/"
echo "   pip install -r requirements.txt"
echo "   python server.py --host 0.0.0.0 --port 8080 &"
echo ""
echo "2️⃣ Install Client (Machine B or same machine):"
echo "   cd $BUILD_DIR/cnaa_local/"
echo "   pip install -r requirements.txt"
echo ""
echo "3️⃣ Run Distributed Tests:"
echo "   cd /root/CNAA-Cloud-Native-Agent-Architecture-"
echo "   python tests/test_distributed_system.py"
echo ""

echo "============================================================================"
echo "✨ PACKAGES READY!"
echo "============================================================================"
echo ""
