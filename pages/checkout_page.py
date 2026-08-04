# pages/checkout_page.py
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class CheckoutPage(BasePage):
    """Page object covering all three checkout steps: the information form,
    the order overview/summary, and the final confirmation screen. Kept as
    one class since SauceDemo treats checkout as a single logical flow
    rather than genuinely separate pages worth splitting out."""

    def __init__(self, page: Page):
        super().__init__(page)
        # Step One: Your Information
        self.first_name_input: Locator = page.locator("#first-name")
        self.last_name_input: Locator = page.locator("#last-name")
        self.postal_code_input: Locator = page.locator("#postal-code")
        self.continue_button: Locator = page.locator("#continue")

        # Step Two: Overview
        self.summary_items: Locator = page.locator(".cart_item")
        self.item_total: Locator = page.locator(".summary_subtotal_label")
        self.tax_label: Locator = page.locator(".summary_tax_label")
        self.total_label: Locator = page.locator(".summary_total_label")
        self.finish_button: Locator = page.locator("#finish")

        # Step Three: Complete
        self.confirmation_header: Locator = page.locator(".complete-header")

    def fill_checkout_information(self, first_name: str, last_name: str, postal_code: str):
        """Fills Step One (personal details) and advances to Step Two."""
        self.first_name_input.fill(first_name)
        self.last_name_input.fill(last_name)
        self.postal_code_input.fill(postal_code)
        self.continue_button.click()

    def get_order_summary_item_names(self) -> list[str]:
        """Returns the product names listed in the Step Two order overview."""
        return self.summary_items.locator(".inventory_item_name").all_inner_texts()

    def finish_order(self):
        self.finish_button.click()
