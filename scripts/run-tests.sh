#!/bin/bash
# NSE Data ETL Test Runner Script
# Runs comprehensive test suite with coverage reporting

set -e

echo "🧪 Running NSE Data ETL test suite..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Default test options
TEST_TYPE=${1:-"all"}
COVERAGE=${COVERAGE:-"true"}
PARALLEL=${PARALLEL:-"true"}

# Function to run tests with specific markers
run_tests() {
    local marker=$1
    local description=$2
    
    echo "📋 Running $description..."
    
    local cmd="pytest"
    
    if [ "$marker" != "all" ]; then
        cmd="$cmd -m $marker"
    fi
    
    if [ "$COVERAGE" = "true" ]; then
        cmd="$cmd --cov=src/nse_etl --cov-branch --cov-report=term-missing"
    fi
    
    if [ "$PARALLEL" = "true" ] && [ "$marker" != "performance" ]; then
        cmd="$cmd -n auto"
    fi
    
    # Add verbose output for CI/CD
    if [ "$CI" = "true" ]; then
        cmd="$cmd -v --tb=short"
    fi
    
    eval $cmd
}

# Function to generate reports
generate_reports() {
    echo "📊 Generating test reports..."
    
    # Generate HTML coverage report
    if [ "$COVERAGE" = "true" ]; then
        pytest --cov=src/nse_etl --cov-branch --cov-report=html --cov-report=xml tests/
        echo "📈 Coverage reports generated:"
        echo "  - HTML: htmlcov/index.html"
        echo "  - XML: coverage.xml"
    fi
    
    # Generate JUnit XML for CI/CD
    if [ "$CI" = "true" ]; then
        pytest --junitxml=junit.xml tests/
        echo "📋 JUnit report generated: junit.xml"
    fi
}

# Main execution
case $TEST_TYPE in
    "unit")
        run_tests "unit" "unit tests"
        ;;
    "integration") 
        run_tests "integration" "integration tests"
        ;;
    "performance")
        run_tests "performance" "performance tests"
        ;;
    "fast")
        run_tests "not slow" "fast tests only"
        ;;
    "slow")
        run_tests "slow" "slow tests only"
        ;;
    "reports")
        generate_reports
        ;;
    "all"|*)
        echo "🔄 Running all test categories..."
        run_tests "unit" "unit tests"
        run_tests "integration" "integration tests" 
        run_tests "performance" "performance tests"
        generate_reports
        ;;
esac

echo ""
echo "✅ Test execution completed!"

# Check coverage threshold
if [ "$COVERAGE" = "true" ]; then
    echo "📊 Checking coverage threshold (90%)..."
    coverage report --fail-under=90 || {
        echo "❌ Coverage below 90% threshold"
        exit 1
    }
    echo "✅ Coverage threshold met"
fi

echo ""
echo "Test summary commands:"
echo "- scripts/run-tests.sh unit        : Run unit tests only"
echo "- scripts/run-tests.sh integration : Run integration tests only"
echo "- scripts/run-tests.sh performance : Run performance tests only"
echo "- scripts/run-tests.sh fast        : Run fast tests only"
echo "- scripts/run-tests.sh reports     : Generate reports only"