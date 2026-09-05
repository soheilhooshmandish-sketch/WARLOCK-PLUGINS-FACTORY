"""Compat shim. Prefer realtime_safety.scan_file."""
from .realtime_safety import scan, scan_file

__all__ = ["scan", "scan_file"]
