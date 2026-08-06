#!/bin/bash
# ============================================================================
# CNAA Distributed System Test Runner
# Run all distributed tests or individual test scenarios
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}ℹ️  ${NC}$1"; }
log_warn() { echo -e "${YELLOW}⚠️  ${NC}$1"; }
log_error() { echo -e "${RED}❌ ${NC}$1"; }
log_step() { echo -e "${BLUE}▶️   ${NC}$1"; }

# ============================================================================
# Functions
# ============================================================================

show_help() {
    echo "CNAA Distributed System Test Runner"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  all              Run all distributed tests (default)"
    echo "  cloud-only       Test cloud server standalone operation only"
    echo "  http-communication Test HTTP client communication only"
    echo "  distributed      Test full distributed flow only"
    echo "  concurrent       Test multiple agents concurrently"
    echo "  network          Test network failure handling"
    echo "  cleanup          Stop any running test servers and cleanup"
    echo "  help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 all                  # Run all tests"
    echo "  $0 http-communication   # Run specific test"
    echo ""
}

run_all_tests() {
    log_step "Running complete distributed system test suite..."
    
    cd "$PROJECT_ROOT"
    
    python3 tests/test_distributed_system.py
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_info "✅ All distributed tests passed!"
    else
        log_error "Some tests failed. Check output above."
    fi
    
    return $EXIT_CODE
}

run_cloud_test() {
    log_step "Running cloud server standalone test..."
    
    cd "$PROJECT_ROOT"
    python3 tests/test_distributed_system.py -k "test_a_cloud_server_standalone"
}

run_http_test() {
    log_step "Running HTTP communication test..."
    
    cd "$PROJECT_ROOT"
    python3 tests/test_distributed_system.py -k "test_b_local_client_http_communication"
}

run_distributed_test() {
    log_step "Running full distributed flow test..."
    
    cd "$PROJECT_ROOT"
    python3 tests/test_distributed_system.py -k "test_c_full_distributed_flow"
}

run_concurrent_test() {
    log_step "Running multi-agent concurrent test..."
    
    cd "$PROJECT_ROOT"
    python3 tests/test_distributed_system.py -k "test_d_multiple_agents_concurrent"
}

run_network_test() {
    log_step "Running network failure handling test..."
    
    cd "$PROJECT_ROOT"
    python3 tests/test_distributed_system.py -k "test_e_network_failure_handling"
}

cleanup() {
    log_info "Cleaning up test resources..."
    
    # Kill any leftover processes on test ports
    for PORT in 8081 8082 8083 8084 8085; do
        PID=$(lsof -t -i:$PORT 2>/dev/null || true)
        if [ -n "$PID" ]; then
            log_warn "Killing process on port $PORT (PID: $PID)"
            kill -9 $PID 2>/dev/null || true
        fi
    done
    
    # Remove temp directories
    TEMP_DIRS=$(find /tmp -maxdepth 1 -name "cnaa_test_*" -type d 2>/dev/null || true)
    if [ -n "$TEMP_DIRS" ]; then
        log_warn "Removing temporary test directories..."
        rm -rf $TEMP_DIRS
    fi
    
    log_info "Cleanup complete"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local command="${1:-all}"
    
    case "$command" in
        all)
            run_all_tests
            ;;
        cloud-only|cloud)
            run_cloud_test
            ;;
        http-communication|http)
            run_http_test
            ;;
        distributed|full)
            run_distributed_test
            ;;
        concurrent)
            run_concurrent_test
            ;;
        network)
            run_network_test
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
