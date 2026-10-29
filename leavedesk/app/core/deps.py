"""Shared route policy.

Every route requires a session (via get_current_user) unless its path is listed here.
tests/test_security_baseline.py walks the route table against this list, so a new route
is protected by default and a public one must be added deliberately (R29a).
"""

PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/healthz",
        # R1-R3: sign-in, invite accept, password reset.
        "/api/v1/auth/login",
        "/api/v1/auth/invite/accept",
        "/api/v1/auth/reset/request",
        "/api/v1/auth/reset/confirm",
    }
)
