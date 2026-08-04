# pages/base_page.py
from playwright.sync_api import Page


class BasePage:
    """Shared base class for all page objects. Holds the Playwright `page`
    handle and any navigation behavior common to every screen."""

    def __init__(self, page: Page):
        self.page = page

    def navigate_to(self, url: str):
        """Navigates to the given URL, waiting only for domcontentloaded
        (not full network idle) to keep navigation fast for this lightweight
        demo app."""
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
