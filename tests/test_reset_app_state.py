# tests/test_reset_app_state.py
"""Covers TC-10: verifies 'Reset App State' clears the cart and returns the
app to its default (no selections) state.
"""
import pytest
from playwright.sync_api import expect

from page_registry import PageRegistry


@pytest.mark.authenticated
def test_reset_app_state_clears_cart(pages: PageRegistry):
    """TC-10: Adds products to the cart, triggers Reset App State from the
    side menu, and verifies the cart badge disappears (count returns to 0)."""
    inventory = pages.inventory_page

    for product_name in inventory.get_all_product_names()[:2]:
        inventory.add_product_to_cart(product_name)
    assert inventory.get_cart_count() == 2

    inventory.reset_app_state()

    expect(inventory.cart_badge).to_have_count(0)
    assert inventory.get_cart_count() == 0
