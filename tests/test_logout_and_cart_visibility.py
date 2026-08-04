# tests/test_logout_and_cart_visibility.py
"""Covers TC-3 (logout) and TC-4 (cart icon visibility) - both quick,
independent checks on an already-authenticated session, so both carry
@pytest.mark.authenticated (storage_state reuse via conftest.py) rather
than logging in via the UI.
"""
import pytest
from playwright.sync_api import expect

from page_registry import PageRegistry


@pytest.mark.smoke
@pytest.mark.authenticated
def test_logout_functionality(pages: PageRegistry):
    """TC-3: Logs out from an authenticated session and verifies the user
    is redirected back to the login screen."""
    pages.inventory_page.logout()
    expect(pages.login_page.login_button).to_be_visible()


@pytest.mark.smoke
@pytest.mark.authenticated
def test_cart_icon_visibility(pages: PageRegistry):
    """TC-4: Verifies the cart icon is visible on the product listing page
    immediately after login."""
    expect(pages.inventory_page.cart_icon).to_be_visible()
