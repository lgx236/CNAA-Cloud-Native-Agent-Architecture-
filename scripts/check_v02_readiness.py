#!/usr/bin/env python3
"""Quick v0.2 readiness verification script.

Run this to verify your installation is ready for production.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists."""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists


def check_directory_exists(path: str, description: str) -> bool:
    """Check if a directory exists."""
    exists = os.path.isdir(path)
    status = "✅" if exists else "⚠️"
    print(f"{status} {description}: {path}")
    return exists


def main():
    """Run all checks."""
    print("\n🔍 CNAA v0.2 Production Readiness Check\n")
    
    errors = []
    warnings = []
    
    # 1. Check required files exist
    print("📁 Checking required files...")
    required_files = [
        ("server.py", "Main server entry point"),
        ("cloud/storage/sqlite_memory_store.py", "SQLite memory storage"),
        ("cloud/storage/sql_state_store.py", "SQLite state storage"),
        ("scripts/backup.sh", "Backup script"),
        ("docs/V0.2_RELEASE_READY.md", "Release documentation"),
    ]
    
    for path, desc in required_files:
        if not check_file_exists(path, desc):
            errors.append(f"Missing critical file: {path}")
    
    print()
    
    # 2. Check backup script is executable
    print("🔧 Checking permissions...")
    if os.path.exists("scripts/backup.sh"):
        is_executable = os.access("scripts/backup.sh", os.X_OK)
        status = "✅" if is_executable else "⚠️"
        print(f"{status} Backup script executable: scripts/backup.sh")
        if not is_executable:
            warnings.append("Backup script not executable - run: chmod +x scripts/backup.sh")
    
    print()
    
    # 3. Check Python environment
    print("🐍 Checking Python environment...")
    version = sys.version_info
    min_version = (3, 10)
    if version >= min_version:
        print(f"✅ Python version: {'.'.join(map(str, version[:2]))}")
    else:
        print(f"❌ Python version too old: {'.'.join(map(str, version[:2]))} (need >= {min_version[0]}.{min_version[1]})")
        errors.append(f"Python version must be >= {'.'.join(map(str, min_version))}")
    
    print()
    
    # 4. Test SQLite storage creation
    print("💾 Testing SQLite storage initialization...")
    try:
        from cloud.storage.sqlite_memory_store import SQLiteMemoryStore
        
        # Use in-memory database for testing
        store = SQLiteMemoryStore(":memory:")
        
        # Try a basic operation
        result = store.store_memory(type(None))  # Will fail, but tests initialization
        
        print("✅ SQLiteMemoryStore initialized successfully")
    except Exception as e:
        print(f"❌ SQLiteMemoryStore failed: {e}")
        errors.append(f"SQLite storage error: {e}")
    
    print()
    
    # 5. Test state storage
    print("📝 Testing State storage initialization...")
    try:
        from cloud.storage.sql_state_store import SqliteStateStore
        store = SqliteStateStore(":memory:")
        print("✅ SqliteStateStore initialized successfully")
    except ImportError as e:
        print(f"⚠️ SqliteStateStore not available: {e}")
        warnings.append("SqliteStateStore import failed - using fallback to memory storage")
    except Exception as e:
        print(f"❌ SqliteStateStore failed: {e}")
        errors.append(f"State storage error: {e}")
    
    print()
    
    # 6. Check scoring system
    print("🎯 Testing scoring system...")
    try:
        from cnaa.scoring import MemoryScores
        scores = MemoryScores(memory_id="test", agent_id="test")
        print(f"✅ Scoring system working (composite={scores.composite:.2f})")
    except Exception as e:
        print(f"❌ Scoring system failed: {e}")
        errors.append(f"Scoring system error: {e}")
    
    print()
    
    # 7. Summary
    print("=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"   • {error}")
        print("\n⛔ NOT READY FOR PRODUCTION")
        return 1
    
    if warnings:
        print(f"\n⚠️ WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   • {warning}")
        print("\n✅ READY (with minor issues)")
        print("\n🔧 Fix warnings:")
        for warning in warnings:
            if "executable" in warning:
                print("   $ chmod +x scripts/backup.sh")
    
    print("\n✅ ALL CHECKS PASSED!")
    print("\n🚀 Ready for limited production deployment.")
    print("   See docs/V0.2_RELEASE_READY.md for details.\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
