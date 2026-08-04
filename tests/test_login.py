# tests/test_login.py
"""Covers TC-1 and TC-2: login behavior across SauceDemo's predefined users,
plus invalid-credential handling. These tests deliberately use the plain
`pages` fixture (not `authenticated_pages`), since they're exercising the
login flow itself.
"""
import pytest
from playwright.sync_api import expect

from page_registry import PageRegistry


@pytest.mark.smoke
@pytest.mark.parametrize(
    "user_key",
    ["standard_user", "problem_user", "performance_glitch_user",
     "error_user", "visual_user", "locked_out_user"],
)
def test_login_with_various_predefined_users(pages: PageRegistry, test_data, base_url, user_key):
    """TC-1: Logs in with each predefined SauceDemo user and verifies the
    expected outcome - a successful redirect to the Products page for
    normal users, or a lockout error for locked_out_user."""
    pages.login_page.navigate_to(base_url)
    credentials = test_data["users"][user_key]
    pages.login_page.login(credentials["username"], credentials["password"])

    if credentials["expected"] == "success":
        expect(pages.inventory_page.page_title).to_have_text("Products")
    else:
        expect(pages.login_page.error_message).to_contain_text("locked out")


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize("attempt_index", range(3))
def test_login_with_invalid_credentials(pages: PageRegistry, test_data, base_url, attempt_index):
    """TC-2: Attempts login using each invalid credential combination from
    test_data.json (wrong password, missing username, missing password)
    and verifies the corresponding error message is shown."""
    invalid_case = test_data["invalid_login_attempts"][attempt_index]
    pages.login_page.navigate_to(base_url)
    pages.login_page.login(invalid_case["username"], invalid_case["password"])
    expect(pages.login_page.error_message).to_contain_text(invalid_case["expected_error"])
