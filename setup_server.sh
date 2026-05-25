#!/bin/bash
# Setup script for Ubuntu/Linux server with Python 3.10
# This script sets up the telegram-bot environment with datetime.UTC compatibility patch

set -e

echo "=========================================="
echo "Telegram Bot - Server Setup Script"
echo "=========================================="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Project Root: $PROJECT_ROOT"

# Step 1: Check Python version
echo ""
echo "[STEP 1] Checking Python version..."
PYTHON_VERSION=$(python3 --version)
echo "Python: $PYTHON_VERSION"

if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "✓ Python >= 3.11 detected - no datetime.UTC patch needed"
else
    echo "⚠ Python < 3.11 detected - datetime.UTC patch will be applied"
fi

# Step 2: Create virtual environment if it doesn't exist
echo ""
echo "[STEP 2] Setting up virtual environment..."
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "Creating new virtual environment..."
    python3 -m venv "$PROJECT_ROOT/.venv"
else
    echo "✓ Virtual environment already exists"
fi

# Step 3: Activate virtual environment
echo ""
echo "[STEP 3] Activating virtual environment..."
source "$PROJECT_ROOT/.venv/bin/activate"
echo "✓ Virtual environment activated"
echo "Python: $(python --version)"

# Step 4: Install requirements
echo ""
echo "[STEP 4] Installing requirements..."
pip install --upgrade pip setuptools wheel
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    pip install -r "$PROJECT_ROOT/requirements.txt"
    echo "✓ Requirements installed"
else
    echo "⚠ requirements.txt not found"
fi

# Step 5: Verify patch_datetime.py exists
echo ""
echo "[STEP 5] Verifying datetime patch..."
if [ -f "$PROJECT_ROOT/patch_datetime.py" ]; then
    echo "✓ patch_datetime.py found"
else
    echo "⚠ patch_datetime.py not found in $PROJECT_ROOT"
fi

# Step 6: Verify ai-agent-assistant path
echo ""
echo "[STEP 6] Checking ai-agent-assistant repository..."
AI_AGENT_PATH="${AI_AGENT_ASSISTANT_PATH:-$(dirname "$PROJECT_ROOT")/ai-agent-assistant}"
if [ -d "$AI_AGENT_PATH" ]; then
    echo "✓ ai-agent-assistant found at: $AI_AGENT_PATH"
else
    echo "⚠ ai-agent-assistant not found at: $AI_AGENT_PATH"
    echo "   Set AI_AGENT_ASSISTANT_PATH environment variable if in different location"
fi

# Step 7: Test datetime patch
echo ""
echo "[STEP 7] Testing datetime patch..."
python3 << 'PYTHON_TEST'
import sys
try:
    import patch_datetime
    from datetime import UTC
    print("✓ datetime.UTC patch successful")
    print(f"  datetime.UTC = {UTC}")
except Exception as e:
    print(f"✗ datetime.UTC patch failed: {e}")
    sys.exit(1)
PYTHON_TEST

# Step 8: Run integration test
echo ""
echo "[STEP 8] Running integration tests..."
if [ -f "$PROJECT_ROOT/test_ai_integration.py" ]; then
    python "$PROJECT_ROOT/test_ai_integration.py"
    echo "✓ Integration tests completed"
else
    echo "⚠ test_ai_integration.py not found"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the telegram bot:"
echo "  source .venv/bin/activate"
echo "  python -m uvicorn webhooks:app --host 0.0.0.0 --port 8000"
echo ""
echo "Or with reload for development:"
echo "  python -m uvicorn webhooks:app --reload --host 0.0.0.0 --port 8000"
echo ""
