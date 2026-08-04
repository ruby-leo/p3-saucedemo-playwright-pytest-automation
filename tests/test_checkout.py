# tests/test_checkout.py
"""Covers TC-8: full checkout flow, from adding known products through to
order confirmation. Kept independent of test_cart_flow.py's random
selection, since checkout needs deterministic, known product data to
reliably verify the order summary contents.
"""
import allure
import pytest
from playwright.sync_api import expect

from page_registry import PageRegistry

CHECKOUT_PRODUCTS = ["Sauce Labs Backpack", "Sauce Labs Bike Light"]


@pytest.mark.authenticated
def test_complete_checkout_and_validate_order(pages: PageRegistry, test_data, page):
    """TC-8: Adds known products to the cart, proceeds through checkout,
    captures a screenshot of the order summary (attached to the Allure
    report), finalizes the order, and verifies the confirmation message."""
    inventory = pages.inventory_page
    for product_name in CHECKOUT_PRODUCTS:
        inventory.add_product_to_cart(product_name)

    inventory.open_cart()
    pages.cart_page.click_checkout()

    checkout_info = test_data["checkout_info"]
    checkout = pages.checkout_page
    checkout.fill_checkout_information(
        checkout_info["first_name"],
        checkout_info["last_name"],
        checkout_info["postal_code"],
    )

    # Verify the order summary lists exactly the products that were added
    summary_item_names = checkout.get_order_summary_item_names()
    assert sorted(summary_item_names) == sorted(CHECKOUT_PRODUCTS), (
        f"Order summary {summary_item_names} does not match added products {CHECKOUT_PRODUCTS}"
    )

    # Capture and attach a screenshot of the order summary before finalizing
    allure.attach(
        page.screenshot(full_page=True),
        name="order_summary_before_finish",
        attachment_type=allure.attachment_type.PNG,
    )

    checkout.finish_order()
    expect(checkout.confirmation_header).to_contain_text("Thank you for your order")
