"""
Datetime Compatibility Patch Module
Import this FIRST before any other imports to fix datetime.UTC issues on Python < 3.11
"""

import sys
import datetime as _dt

def patch_datetime_utc():
    """
    Patch datetime module to provide UTC for Python < 3.11
    
    Python 3.11+ has datetime.UTC
    Python 3.10 and earlier only have datetime.timezone.utc
    
    This function makes datetime.UTC available by aliasing it to timezone.utc
    on older Python versions.
    """
    if sys.version_info < (3, 11):
        if not hasattr(_dt, "UTC"):
            # Make UTC available as an attribute
            _dt.UTC = _dt.timezone.utc
            
            # Update the module's __all__ if it exists
            if hasattr(_dt, "__all__"):
                _dt.__all__.append("UTC")

# Apply patch immediately on import
patch_datetime_utc()
