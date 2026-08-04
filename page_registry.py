# page_registry.py
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage


class PageRegistry:
    """Lazily instantiates and hands out page objects for a given Playwright
    `page`, so tests never construct page objects directly - see the
    `pages` / `authenticated_pages` fixtures in conftest.py."""

    def __init__(self, page):
        self.page = page
        self._login_page = None
        self._inventory_page = None
        self._cart_page = None
        self._checkout_page = None

    @property
    def login_page(self) -> LoginPage:
        if not self._login_page:
            self._login_page = LoginPage(self.page)
        return self._login_page

    @property
    def inventory_page(self) -> InventoryPage:
        if not self._inventory_page:
            self._inventory_page = InventoryPage(self.page)
        return self._inventory_page

    @property
    def cart_page(self) -> CartPage:
        if not self._cart_page:
            self._cart_page = CartPage(self.page)
        return self._cart_page

    @property
    def checkout_page(self) -> CheckoutPage:
        if not self._checkout_page:
            self._checkout_page = CheckoutPage(self.page)
        return self._checkout_page
