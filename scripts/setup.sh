#!/bin/bash
# NSE Data ETL Development Setup Script
# This script sets up the development environment

set -e  # Exit on any error

echo "🚀 Setting up NSE Data ETL development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
required_version="3.9"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "❌ Python 3.9+ is required. Found: Python $python_version"
    exit 1
fi

echo "✅ Python version check passed: Python $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install development dependencies
echo "📚 Installing development dependencies..."
pip install -e ".[dev]"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your specific configuration"
fi

# Install pre-commit hooks
echo "🎣 Installing pre-commit hooks..."
pre-commit install

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs data tmp

# Run initial code quality checks
echo "🔍 Running initial code quality checks..."
echo "Running Black formatter..."
black --check src/ tests/ || echo "⚠️  Some files need formatting"

echo "Running isort..."
isort --check-only src/ tests/ || echo "⚠️  Some imports need sorting"

echo "Running flake8..."
flake8 src/ tests/ || echo "⚠️  Some linting issues found"

echo "Running MyPy type checking..."
mypy src/ || echo "⚠️  Some type issues found"

# Run tests to ensure everything is working
echo "🧪 Running tests..."
pytest tests/ -v --tb=short || echo "⚠️  Some tests failed"

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Run 'source venv/bin/activate' to activate the virtual environment"
echo "3. Run 'docker-compose up -d' to start development services"
echo "4. Run 'python -m nse_etl.main' to start the application"
echo ""
echo "Useful commands:"
echo "- scripts/run-tests.sh     : Run all tests"
echo "- scripts/run-linting.sh   : Run code quality checks"
echo "- scripts/run-dev.sh       : Start development server"
echo "- scripts/build-docker.sh  : Build Docker image"