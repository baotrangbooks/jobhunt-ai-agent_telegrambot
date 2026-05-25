"""
Sitecustomize: Patches Python environment BEFORE any imports run.
This is imported automatically by Python at startup.

Specifically fixes the datetime.UTC import issue for Python < 3.11
that prevents ai-agent-assistant from loading.
"""

import sys
import datetime as _dt

# Patch datetime.UTC for Python < 3.11 compatibility
# This must run BEFORE any other imports that depend on datetime.UTC
if sys.version_info < (3, 11):
    # Python 3.10 and earlier don't have datetime.UTC
    # Use timezone.utc as equivalent
    if not hasattr(_dt, "UTC"):
        _dt.UTC = _dt.timezone.utc
        # Also make it available via from datetime import UTC
        import importlib.abc
        import importlib.machinery
        
        # Record that we patched datetime
        _dt._patched_utc = True
