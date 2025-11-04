"""
Session storage module.

This module is separated from session.py to avoid circular import issues.
Routes can import both Session class and sessions dict without creating cycles.

In production, replace this in-memory dict with:
- Redis for distributed systems
- Database for persistence
- Memcached for caching layer
"""

# In-memory session storage
# WARNING: Sessions will be lost on server restart
sessions = {}
