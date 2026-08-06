#!/usr/bin/env python3
"""Verify Cloud-Local endpoint communication."""

import sys
import os

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from datetime import datetime


def test_cloud_endpoint():
    """Test if cloud server is running."""
    print("Testing Cloud Endpoint...")
    
    try:
        from local.client.mcp_client_real import CNAA_MCPClient
        
        client = CNAA_MCPClient(
            server_url="http://localhost:8080",
            timeout=10
        )
        
        # Health check
        if not client.health_check():
            print("❌ FAIL: Cloud server not reachable")
            print("   Solution: ./scripts/start.sh")
            return False
        
        print("✅ PASS: Cloud server is healthy")
        return True
        
    except ImportError as e:
        print(f"❌ FAIL: Cannot import MCP client: {e}")
        print("   Make sure you installed the package: pip install -e .")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error testing cloud endpoint: {e}")
        return False


def test_store_memory():
    """Test storing memory on cloud."""
    print("\nTesting Store Memory...")
    
    try:
        from local.client.mcp_client_real import CNAA_MCPClient
        
        client = CNAA_MCPClient(server_url="http://localhost:8080")
        
        result = client.store_memory(
            agent_id="test-agent",
            memory_id=f"test-{int(datetime.now().timestamp())}",
            memory_type="long_term",
            content={"message": "Testing cloud-local communication"},
            tags=["test", "demo"],
            completion_score=1.0
        )
        
        if result.get("status") == "ok":
            print("✅ PASS: Successfully stored memory on cloud")
            return True
        else:
            print(f"❌ FAIL: {result}")
            return False
            
    except ConnectionError as e:
        print(f"❌ FAIL: Cannot connect to cloud server: {e}")
        print("   Make sure cloud server is running: ./scripts/start.sh")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error storing memory: {e}")
        return False


def test_list_memories():
    """Test retrieving memories from cloud."""
    print("\nTesting List Memories...")
    
    try:
        from local.client.mcp_client_real import CNAA_MCPClient
        
        client = CNAA_MCPClient(server_url="http://localhost:8080")
        
        result = client.list_memories(agent_id="test-agent", limit=10)
        
        if result.get("status") == "ok":
            count = len(result.get("memories", []))
            print(f"✅ PASS: Retrieved {count} memories from cloud")
            return True
        else:
            print(f"❌ FAIL: {result}")
            return False
            
    except ConnectionError as e:
        print(f"❌ FAIL: Cannot connect to cloud server: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error listing memories: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("CNAA v0.2 - Cloud-Local Endpoint Verification")
    print("=" * 60)
    print()
    
    tests = [
        ("Cloud Server Reachability", test_cloud_endpoint),
        ("Store Memory (Cloud Write)", test_store_memory),
        ("List Memories (Cloud Read)", test_list_memories),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'─' * 60}")
        print(f"Test: {name}")
        print(f"{'─' * 60}")
        try:
            results.append(test_func())
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
            print("\n")
    
    # Summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print()
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Your Cloud-Local dual endpoint architecture is working correctly:")
        print("  ✅ Local Client: Real HTTP client communicating with cloud")
        print("  ✅ Cloud Server: Accepting requests and persisting data")
        print("  ✅ Communication: Over-the-network HTTP/MCP protocol")
        print()
        print("You can now use this in your agent application!")
        exit(0)
    else:
        print()
        print("⚠️  SOME TESTS FAILED")
        print()
        print("Troubleshooting steps:")
        print("  1. Make sure cloud server is running: ./scripts/start.sh")
        print("  2. Check network connectivity: curl http://localhost:8080/health")
        print("  3. Review firewall settings if using remote server")
        print("  4. Check logs: cat logs/cnaa.log")
        exit(1)
    
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
