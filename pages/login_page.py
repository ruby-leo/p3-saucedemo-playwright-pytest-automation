# pages/login_page.py
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class LoginPage(BasePage):
    """Page object for SauceDemo's login screen - the site's entry point."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input: Locator = page.locator("#user-name")
        self.password_input: Locator = page.locator("#password")
        self.login_button: Locator = page.locator("#login-button")
        self.error_message: Locator = page.locator('[data-test="error"]')

    def login(self, username: str, password: str):
        """Fills both credential fields and submits the login form."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
