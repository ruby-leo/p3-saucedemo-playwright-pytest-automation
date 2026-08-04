# utilities/api_client.py
"""Thin wrapper around Playwright's APIRequestContext for non-UI checks.

SauceDemo is a fully client-side rendered demo app - product, cart, and
checkout data all live inside its JS bundle rather than behind a real REST
API - so there isn't a genuine data-seeding API to call here the way you
might on an app with an actual backend. The one legitimate API-level use in
this suite is a fast pre-flight reachability check, run once per test
session before any browser is launched: if the site itself is down, the
whole suite fails in milliseconds with one clear message instead of dozens
of individual UI test timeouts.
"""
from playwright.sync_api import APIRequestContext


def verify_site_is_reachable(request_context: APIRequestContext, base_url: str) -> None:
    """Sends a lightweight GET request to base_url and raises if the site
    doesn't respond successfully. Intended to run once per test session,
    before any browser-based test begins.
    """
    response = request_context.get(base_url)
    if not response.ok:
        raise RuntimeError(
            f"Pre-flight check failed: {base_url} responded with "
            f"HTTP {response.status}. Aborting test session before "
            f"launching any browsers."
        )
