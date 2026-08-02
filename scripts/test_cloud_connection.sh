#!/bin/bash
# Test Cloud Connection - Quick verification script

set -e

echo "🔍 Testing CNAA Cloud Server Connection\n"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ No .env file found!"
    echo "   Creating from template..."
    cp .env.example .env
fi

# Load environment variables
source .env

# Check configuration
if [ -z "$CNAA_SERVER_URL" ]; then
    echo "❌ CNAA_SERVER_URL not configured in .env"
    exit 1
fi

echo "✅ Configured Cloud URL: $CNAA_SERVER_URL"

# Try health check
echo "📡 Testing connection..."
response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$CNAA_SERVER_URL/health" 2>/dev/null || echo "000")

if [ "$response" = "200" ]; then
    echo "✅ Cloud server is reachable!"
    
    # Get actual response
    data=$(curl -s "$CNAA_SERVER_URL/health")
    echo "   Response preview: ${data:0:100}..."
else
    echo "❌ Cannot connect to cloud server!"
    echo "   HTTP Status: $response"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Verify CNAA_SERVER_URL is correct"
    echo "   2. Check firewall allows outbound connections"
    echo "   3. Ensure cloud server is running"
    echo "   4. Test manually: curl http://$CNAA_SERVER_URL/health"
    exit 1
fi

# Check API key
if [ -n "$CNAA_SERVER_API_KEY" ] && [[ "$CNAA_SERVER_API_KEY" != *"your-api-key-here"* ]]; then
    echo "✅ API Key configured"
elif [ -n "$CNAA_SERVER_API_KEY" ] && [[ "$CNAA_SERVER_API_KEY" == *"your-api-key-here"* ]]; then
    echo "⚠️  Using placeholder API key - change in production"
else
    echo "⚠️  No API Key - authentication disabled on client"
    echo "   Make sure cloud server allows unauthenticated requests"
fi

echo ""
echo "✅ Connection test successful!"
echo ""
echo "Next steps:"
echo "  1. Start local agent applications"
echo "  2. Data will sync to: $CNAA_SERVER_URL"
echo "  3. Local databases: $CNAA_DB_PATH, $CNAA_STATE_DB_PATH"
