#!/bin/bash
# Test runner script for CNAA - Supports full test suite, subsets, and coverage reporting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NUM_WORKERS=${NUM_WORKERS:-4}  # Parallel workers
COVERAGE_THRESHOLD=80         # Minimum coverage percentage
RUN_LARGE_TESTS=false        # Default: skip large-scale tests

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --large-tests) 
            RUN_LARGE_TESTS=true
            shift
            ;;
        --unit-only)
            UNIT_ONLY=true
            shift
            ;;
        --integration)
            INTEGRATION_ONLY=true
            shift
            ;;
        --performance)
            PERFORMANCE_ONLY=true
            shift
            ;;
        --coverage-report)
            GENERATE_COVERAGE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --large-tests      Run large-scale performance tests"
            echo "  --unit-only        Run only unit tests (exclude integration)"
            echo "  --integration      Run only integration tests"
            echo "  --performance      Run only performance/benchmark tests"
            echo "  --coverage-report  Generate detailed coverage report"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Count test files
TOTAL_FILES=$(ls tests/test_*.py 2>/dev/null | wc -l)
echo -e "${BLUE}📊 CNAA Test Suite Runner${NC}"
echo "========================================="
echo "Total test files: $TOTAL_FILES"
echo "Workers: $NUM_WORKERS"
if [ "$RUN_LARGE_TESTS" = true ]; then
    echo -e "${YELLOW}⚠️  Large-scale tests ENABLED${NC}"
else
    echo -e "${YELLOW}⚠️  Large-scale tests DISABLED (skip mega tests)${NC}"
fi
echo ""

# Function to run specific test category
run_tests() {
    local filter=""
    local description=""
    
    if [ "$UNIT_ONLY" = true ]; then
        filter="-m \"unit\" "
        description="Unit Tests Only"
    elif [ "$INTEGRATION_ONLY" = true ]; then
        filter="-m \"integration\" "
        description="Integration Tests Only"
    elif [ "$PERFORMANCE_ONLY" = true ]; then
        filter="-m \"performance\" "
        description="Performance Tests Only"
    fi
    
    if [ -n "$filter" ]; then
        echo -e "${BLUE}Running: ${description}${NC}"
        pytest $filter tests/ -v -n $NUM_WORKERS
    else
        echo -e "${GREEN}🚀 Running Full Test Suite...${NC}"
        
        if [ "$RUN_LARGE_TESTS" = true ]; then
            echo -e "${YELLOW}✅ Including large-scale tests${NC}"
            pytest tests/ \
                -v \
                -n $NUM_WORKERS \
                -m "not slow" \
                --tb=short
        else
            echo -e "${YELLOW}⏭️  Skipping large-scale tests${NC}"
            pytest tests/ \
                -v \
                -n $NUM_WORKERS \
                -m "not (slow or large)" \
                --tb=short
        fi
    fi
}

# Function to run with coverage
run_with_coverage() {
    echo -e "${BLUE}Running tests with coverage analysis...${NC}"
    
    if [ "$RUN_LARGE_TESTS" = true ]; then
        pytest tests/ \
            --cov=cnaa --cov=cloud --cov=local \
            --cov-report=html --cov-report=term-missing \
            --cov-report=xml \
            -n $NUM_WORKERS \
            --strict-markers
    else
        pytest tests/ \
            --cov=cnaa --cov=cloud --cov=local \
            --cov-report=html --cov-report=term-missing \
            --cov-report=xml \
            -n $NUM_WORKERS \
            -m "not (slow or large)" \
            --strict-markers
    fi
    
    echo ""
    echo -e "${GREEN}✅ Coverage report generated:${NC}"
    echo "  📁 HTML: htmlcov/index.html"
    echo "  📄 XML: coverage.xml"
    echo "  📋 Terminal: See above"
}

# Function to show statistics
show_statistics() {
    echo ""
    echo -e "${BLUE}Test Statistics:${NC}"
    echo "================="
    
    for file in tests/test_*.py; do
        count=$(grep -c "^def test_" "$file" 2>/dev/null || echo 0)
        name=$(basename "$file")
        printf "  %-50s %d tests\n" "$name:" "$count"
    done
    
    total=$(grep -r "^def test_" tests/test_*.py | wc -l)
    echo ""
    echo -e "${GREEN}Total tests across all files:${NC} $total"
}

# Main execution
case "${TEST_RUN_TYPE:-full}" in
    full)
        run_tests
        ;;
    coverage)
        run_with_coverage
        ;;
    stats)
        show_statistics
        ;;
    *)
        run_tests
        ;;
esac

echo ""
echo -e "${GREEN}✅ Test suite completed successfully!${NC}"
