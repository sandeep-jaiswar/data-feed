#!/bin/bash
# NSE Data ETL Code Quality Checker
# Runs all linting and formatting tools

set -e

echo "🔍 Running NSE Data ETL code quality checks..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Configuration
FIX=${1:-"false"}  # Set to "fix" to auto-fix issues
EXIT_ON_ERROR=${EXIT_ON_ERROR:-"true"}

# Function to run a linting tool
run_linter() {
    local tool=$1
    local description=$2
    local command=$3
    local fix_command=$4
    
    echo ""
    echo "📋 Running $description..."
    
    if [ "$FIX" = "fix" ] && [ -n "$fix_command" ]; then
        echo "🔧 Auto-fixing with $tool..."
        eval $fix_command || {
            if [ "$EXIT_ON_ERROR" = "true" ]; then
                echo "❌ $tool auto-fix failed"
                exit 1
            fi
        }
    else
        eval $command || {
            local exit_code=$?
            if [ "$EXIT_ON_ERROR" = "true" ]; then
                echo "❌ $tool check failed"
                exit $exit_code
            else
                echo "⚠️  $tool issues found (continuing...)"
            fi
        }
    fi
}

echo "🎯 Target directories: src/ tests/"

# Black - Code formatting
run_linter "Black" "code formatting" \
    "black --check --diff src/ tests/" \
    "black src/ tests/"

# isort - Import sorting  
run_linter "isort" "import sorting" \
    "isort --check-only --diff src/ tests/" \
    "isort src/ tests/"

# Flake8 - Style and complexity checking
run_linter "Flake8" "style and complexity checking" \
    "flake8 src/ tests/" \
    ""

# MyPy - Type checking
run_linter "MyPy" "type checking" \
    "mypy src/" \
    ""

# Bandit - Security scanning
run_linter "Bandit" "security scanning" \
    "bandit -r src/ -f json -o bandit-report.json || bandit -r src/" \
    ""

# Safety - Dependency vulnerability scanning
run_linter "Safety" "dependency vulnerability scanning" \
    "safety check --json --output safety-report.json || safety check" \
    ""

# Additional checks for specific files
echo ""
echo "📋 Running additional checks..."

# Check pyproject.toml syntax
echo "🔍 Checking pyproject.toml syntax..."
python -c "import tomllib; tomllib.loads(open('pyproject.toml', 'rb').read())" || {
    echo "❌ pyproject.toml syntax error"
    if [ "$EXIT_ON_ERROR" = "true" ]; then exit 1; fi
}

# Check YAML files
echo "🔍 Checking YAML files..."
find . -name "*.yml" -o -name "*.yaml" | grep -v node_modules | while read yaml_file; do
    python -c "import yaml; yaml.safe_load(open('$yaml_file'))" || {
        echo "❌ YAML syntax error in $yaml_file"
        if [ "$EXIT_ON_ERROR" = "true" ]; then exit 1; fi
    }
done

# Check for common issues
echo "🔍 Checking for common issues..."

# Check for TODO/FIXME comments
echo "📝 Checking for TODO/FIXME comments..."
grep -r "TODO\|FIXME\|XXX" src/ tests/ --exclude-dir=__pycache__ || echo "✅ No TODO/FIXME comments found"

# Check for print statements (should use logging)
echo "🖨️  Checking for print statements..."
grep -r "print(" src/ --exclude-dir=__pycache__ && {
    echo "⚠️  Found print statements - consider using logging instead"
} || echo "✅ No print statements found"

# Check for hardcoded secrets patterns
echo "🔐 Checking for potential hardcoded secrets..."
grep -r -E "(password|secret|key|token)\s*=\s*['\"][^'\"]{8,}" src/ --exclude-dir=__pycache__ && {
    echo "⚠️  Potential hardcoded secrets found"
} || echo "✅ No obvious hardcoded secrets found"

echo ""
echo "📊 Code quality summary:"
echo "========================"

if [ "$FIX" = "fix" ]; then
    echo "✅ Auto-fixes applied where possible"
    echo "🔄 Re-run without 'fix' to check remaining issues"
else
    echo "💡 To auto-fix issues, run: scripts/run-linting.sh fix"
fi

echo ""
echo "Generated reports:"
echo "- bandit-report.json : Security scan results"
echo "- safety-report.json : Dependency vulnerability results"
echo ""
echo "Quality check commands:"
echo "- scripts/run-linting.sh      : Check all issues"
echo "- scripts/run-linting.sh fix  : Auto-fix where possible"