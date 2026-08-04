# pages/cart_page.py
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class CartPage(BasePage):
    """Page object for the shopping cart page."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.cart_items: Locator = page.locator(".cart_item")
        self.checkout_button: Locator = page.locator("#checkout")

    def get_cart_item_names(self) -> list[str]:
        return self.cart_items.locator(".inventory_item_name").all_inner_texts()

    def get_cart_item_prices(self) -> list[float]:
        price_texts = self.cart_items.locator(".inventory_item_price").all_inner_texts()
        return [float(p.replace("$", "")) for p in price_texts]

    def click_checkout(self):
        self.checkout_button.click()
