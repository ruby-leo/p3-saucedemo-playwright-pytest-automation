# tests/test_sorting.py
"""Covers TC-9: verifies the product sort dropdown correctly reorders the
listing for every available sort option.
"""
import pytest

from page_registry import PageRegistry

SORT_OPTIONS = [
    ("Name (A to Z)", "name_asc"),
    ("Name (Z to A)", "name_desc"),
    ("Price (low to high)", "price_asc"),
    ("Price (high to low)", "price_desc"),
]


@pytest.mark.regression
@pytest.mark.authenticated
@pytest.mark.parametrize("option_label, expected_order", SORT_OPTIONS)
def test_sorting_functionality(pages: PageRegistry, option_label, expected_order):
    """TC-9: Selects each sort option in turn and asserts the resulting
    product order - by name or by price, ascending or descending as
    expected for that option."""
    inventory = pages.inventory_page
    inventory.sort_by(option_label)

    if expected_order in ("name_asc", "name_desc"):
        names = inventory.get_all_product_names()
        expected = sorted(names, reverse=(expected_order == "name_desc"))
        assert names == expected, f"Products not sorted correctly for '{option_label}': got {names}"
    else:
        prices = inventory.get_all_product_prices()
        expected = sorted(prices, reverse=(expected_order == "price_desc"))
        assert prices == expected, f"Prices not sorted correctly for '{option_label}': got {prices}"
