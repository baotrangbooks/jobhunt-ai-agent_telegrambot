#!/usr/bin/env python3
"""
Diagnostic script to debug ai-agent-assistant import issues step-by-step
Run this on the server to identify why the import fails
"""

import sys
import os
from pathlib import Path
import importlib
import traceback

print("=" * 80)
print("AI AGENT ASSISTANT IMPORT DIAGNOSTIC SCRIPT")
print("=" * 80)

# Step 1: Python version
print("\n[STEP 1] Python Version")
print(f"  Python: {sys.version}")
print(f"  Version Info: {sys.version_info}")

# Step 2: Check datetime.UTC availability
print("\n[STEP 2] Check datetime.UTC Availability")
try:
    from datetime import UTC
    print(f"  ✓ datetime.UTC available: {UTC}")
except ImportError as e:
    print(f"  ✗ datetime.UTC NOT available: {e}")
    print("  → This is the problem! Python version likely < 3.11")
    try:
        import datetime as dt
        print(f"  → But datetime.timezone.utc exists: {dt.timezone.utc}")
    except Exception as e2:
        print(f"  ✗ datetime.timezone.utc also failed: {e2}")

# Step 3: Check sys.path and AI agent path
print("\n[STEP 3] AI Agent Path Configuration")
project_root = Path(__file__).resolve().parent
print(f"  Project Root: {project_root}")

ai_agent_path_env = os.getenv("AI_AGENT_ASSISTANT_PATH")
if ai_agent_path_env:
    ai_agent_path = Path(ai_agent_path_env).expanduser().resolve()
    if ai_agent_path.is_file():
        ai_agent_path = ai_agent_path.parent
    if ai_agent_path.name == "ai_agent_assistant":
        ai_agent_path = ai_agent_path.parent
    print(f"  Using AI_AGENT_ASSISTANT_PATH: {ai_agent_path}")
else:
    ai_agent_path = project_root.parent / "ai-agent-assistant"
    print(f"  Using default path: {ai_agent_path}")

print(f"  Path exists: {ai_agent_path.exists()}")

if ai_agent_path.exists():
    print(f"  Contents:")
    for item in ai_agent_path.iterdir():
        if item.is_dir():
            print(f"    [DIR] {item.name}")
        else:
            print(f"    [FILE] {item.name}")

# Step 4: sys.path
print("\n[STEP 4] sys.path (first 5 entries)")
for i, path in enumerate(sys.path[:5]):
    print(f"  [{i}] {path}")

# Step 5: Try to import ai_agent_assistant directly
print("\n[STEP 5] Try Direct Import: from ai_agent_assistant import build_local_runtime")
if ai_agent_path.exists() and str(ai_agent_path) not in sys.path:
    sys.path.insert(0, str(ai_agent_path))
    print(f"  Added to sys.path[0]: {ai_agent_path}")

try:
    from ai_agent_assistant import build_local_runtime, stream_chat_turn
    print(f"  ✓ SUCCESS! build_local_runtime: {build_local_runtime}")
    print(f"  ✓ SUCCESS! stream_chat_turn: {stream_chat_turn}")
except ImportError as e:
    print(f"  ✗ FAILED with ImportError:")
    print(f"     {e}")
    print(f"\n  Full traceback:")
    traceback.print_exc()
    
    # Try to find where the error originates
    print("\n  [DEBUG] Trying to import ai-agent-assistant module directly...")
    try:
        import ai_agent_assistant
        print(f"    ✓ ai_agent_assistant module found: {ai_agent_assistant}")
        print(f"    Module file: {ai_agent_assistant.__file__}")
        print(f"    Module attributes: {dir(ai_agent_assistant)}")
    except ImportError as e2:
        print(f"    ✗ Module import failed: {e2}")
        traceback.print_exc()

# Step 6: Check if __init__.py exists
print("\n[STEP 6] Check ai-agent-assistant/__init__.py")
init_file = ai_agent_path / "__init__.py"
print(f"  __init__.py exists: {init_file.exists()}")

# Step 7: Environment variables
print("\n[STEP 7] Environment Variables")
print(f"  PYTHONPATH: {os.getenv('PYTHONPATH', 'NOT SET')}")
print(f"  AI_AGENT_ASSISTANT_PATH: {os.getenv('AI_AGENT_ASSISTANT_PATH', 'NOT SET')}")
print(f"  VIRTUAL_ENV: {os.getenv('VIRTUAL_ENV', 'NOT SET')}")

# Step 8: Check installed packages
print("\n[STEP 8] Check Key Packages")
packages_to_check = [
    'langchain',
    'langchain_openai',
    'langchain_community',
    'langgraph',
    'openai',
]

for pkg in packages_to_check:
    try:
        mod = importlib.import_module(pkg)
        version = getattr(mod, '__version__', 'unknown')
        print(f"  ✓ {pkg}: version {version}")
    except ImportError:
        print(f"  ✗ {pkg}: NOT INSTALLED")

# Step 9: Try to run the actual ai_integration module
print("\n[STEP 9] Try to import ai_integration module")
try:
    # Add current project to path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    from ai_integration import AIAgentIntegration, build_local_runtime, stream_chat_turn
    print(f"  ✓ ai_integration imported successfully")
    print(f"  ✓ build_local_runtime available: {build_local_runtime is not None}")
    print(f"  ✓ stream_chat_turn available: {stream_chat_turn is not None}")
except ImportError as e:
    print(f"  ✗ FAILED to import ai_integration:")
    print(f"     {e}")
    traceback.print_exc()

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)

# Summary
print("\nSUMMARY:")
try:
    from datetime import UTC
    print("  ✓ Python version supports datetime.UTC")
except ImportError:
    print("  ✗ Python version does NOT support datetime.UTC (need >=3.11)")
    print("  → SOLUTIONS:")
    print("     1. Upgrade Python to 3.11 or newer")
    print("     2. Or use compatibility shim in ai_integration.py")

if ai_agent_path.exists():
    print(f"  ✓ ai-agent-assistant directory found at {ai_agent_path}")
else:
    print(f"  ✗ ai-agent-assistant directory NOT found at {ai_agent_path}")
    print("  → Set AI_AGENT_ASSISTANT_PATH environment variable or install in correct location")

print("\n")
