"""
MCP Routes package
"""

from routes.health import healthz
from routes.jwks import jwks

__all__ = [
    "healthz",
    "jwks",
]
