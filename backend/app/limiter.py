"""
RemitMind API Rate Limiting Infrastructure
Built on slowapi (limits library) to safeguard high-impact endpoints against brute force and abuse.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    headers_enabled=False,
    strategy="fixed-window"
)
