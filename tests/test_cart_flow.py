# tests/test_cart_flow.py
"""Covers TC-5, TC-6, and TC-7 as a single continuous scenario: random
product selection -> adding those products to the cart -> verifying the
cart's contents match.

These three are combined into one test function rather than three separate
ones because they share state that must flow in order (the same randomly
selected products throughout). Splitting them into independent pytest
items would either require re-deriving the random selection in each test
(defeating the point of using the *same* 4 products end to end) or sharing
mutable state across test functions - which is unsafe once pytest-xdist
distributes tests across parallel worker processes. Keeping it as one
function makes the scenario atomic and safely parallelizable.
"""
import random

import pytest
from playwright.sync_api import expect

from page_registry import PageRegistry


@pytest.mark.authenticated
def test_random_product_selection_add_to_cart_and_verify(pages: PageRegistry):
    """TC-5, TC-6, TC-7: Randomly selects 4 of the 6 listed products, adds
    each to the cart, then verifies the cart badge count and the cart
    page's contents match the selection exactly."""
    inventory = pages.inventory_page

    all_product_names = inventory.get_all_product_names()
    assert len(all_product_names) == 6, (
        f"Expected 6 products on the inventory page, found {len(all_product_names)}"
    )

    # TC-5: randomly select 4 of the 6 products and capture their price data
    selected_products = random.sample(all_product_names, 4)
    selected_prices = {name: inventory.get_product_price(name) for name in selected_products}

    # TC-6: add each selected product to the cart, then verify the cart badge count
    for product_name in selected_products:
        inventory.add_product_to_cart(product_name)

    expect(inventory.cart_badge).to_have_text(str(len(selected_products)))

    # TC-7: open the cart and verify its contents match exactly what was added
    inventory.open_cart()
    cart = pages.cart_page

    cart_item_names = cart.get_cart_item_names()
    assert sorted(cart_item_names) == sorted(selected_products), (
        f"Cart contents {cart_item_names} do not match selected products {selected_products}"
    )

    cart_item_prices = cart.get_cart_item_prices()
    for name, price in zip(cart_item_names, cart_item_prices):
        assert price == selected_prices[name], (
            f"Price mismatch for '{name}': cart shows {price}, expected {selected_prices[name]}"
        )
