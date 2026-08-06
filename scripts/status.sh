#!/bin/bash
# ============================================================================
# CNAA Server Status Script
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/start.sh" status
