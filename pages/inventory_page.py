# pages/inventory_page.py
import re
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class InventoryPage(BasePage):
    """Page object for the product listing ('Products') page shown right
    after login. This is the hub most other flows (cart, sort, reset,
    logout) branch off from."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.page_title: Locator = page.locator(".title")
        self.inventory_items: Locator = page.locator(".inventory_item")
        self.cart_icon: Locator = page.locator(".shopping_cart_link")
        self.cart_badge: Locator = page.locator(".shopping_cart_badge")
        self.sort_dropdown: Locator = page.locator(".product_sort_container")
        self.menu_button: Locator = page.locator("#react-burger-menu-btn")
        self.logout_link: Locator = page.locator("#logout_sidebar_link")
        self.reset_app_state_link: Locator = page.locator("#reset_sidebar_link")

    def get_all_product_names(self) -> list[str]:
        """Returns the names of every product currently listed on the page,
        in their current display order."""
        return self.inventory_items.locator(".inventory_item_name").all_inner_texts()

    def get_all_product_prices(self) -> list[float]:
        """Returns prices for every listed product, in current display
        order - used to assert sort order without depending on names."""
        price_texts = self.inventory_items.locator(".inventory_item_price").all_inner_texts()
        return [float(p.replace("$", "")) for p in price_texts]

    def get_product_price(self, product_name: str) -> float:
        """Returns the price (as a float) for a single named product."""
        item = self.inventory_items.filter(has_text=product_name)
        price_text = item.locator(".inventory_item_price").inner_text()
        return float(price_text.replace("$", ""))

    def add_product_to_cart(self, product_name: str):
        """Clicks 'Add to cart' for the given product. Scoped to that
        product's own item container (rather than a single global button
        locator), since every product has an identically-classed button."""
        item = self.inventory_items.filter(has_text=product_name)
        item.get_by_role("button", name=re.compile("Add to cart", re.IGNORECASE)).click()

    def get_cart_count(self) -> int:
        """Returns the number on the cart badge, or 0 if the badge isn't
        rendered at all - SauceDemo hides the badge entirely when the cart
        is empty rather than showing a literal '0'."""
        if self.cart_badge.count() == 0:
            return 0
        return int(self.cart_badge.inner_text())

    def open_cart(self):
        self.cart_icon.click()

    def sort_by(self, option_label: str):
        """Selects a sort option from the dropdown by its visible label,
        e.g. 'Price (low to high)', 'Name (Z to A)'."""
        self.sort_dropdown.select_option(label=option_label)

    def open_menu(self):
        self.menu_button.click()

    def logout(self):
        """Opens the side menu and clicks Logout - the link isn't
        interactable until the menu is explicitly opened first."""
        self.open_menu()
        self.logout_link.click()

    def reset_app_state(self):
        """Opens the side menu and clicks 'Reset App State'."""
        self.open_menu()
        self.reset_app_state_link.click()
