# SauceDemo E-Commerce Automation — Playwright + Pytest

[![CI/CD Pipeline](https://github.com/ruby-leo/p3-saucedemo-playwright-pytest-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/ruby-leo/p3-saucedemo-playwright-pytest-automation/actions/workflows/ci.yml)
[![Allure Report](https://img.shields.io/badge/Allure-Report-orange?logo=testcafe)](https://ruby-leo.github.io/p3-saucedemo-playwright-pytest-automation/)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Python-2EAD33?logo=playwright)](https://playwright.dev/python/)

A test automation suite for [SauceDemo](https://www.saucedemo.com/), built on **Playwright + plain pytest** covering login, product browsing, cart management, checkout, sorting, and app-state reset.

---

## Highlights

- **Plain pytest** — standard `pytest` test functions, fixtures, and markers — no BDD layer on top.
- **Cross-browser by default** — every test runs against both **Chromium** and **Firefox** automatically via `pytest.ini`, no per-test setup.
- **Parallel execution** — `pytest-xdist` (`-n auto`) distributes tests across all available CPU cores.
- **Authenticated session reuse via `storage_state`** — logs in once per browser per worker, saves the session, and every subsequent test that needs to be logged in reuses it instead of repeating the login UI flow. See [Authenticated session reuse](#authenticated-session-reuse) below.
- **API-level pre-flight check** — a `playwright.request` based reachability check runs once per session before any browser launches, failing fast if the site itself is down.
- **Full visual evidence, every run** — screenshots, videos, and Playwright traces (`retain-on-failure`) are captured for every test and auto-attached to Allure.
- **Self-healing runs** — one automatic retry (`pytest-rerunfailures`) for transient flakiness before a test is marked failed.
- **CI-published reports** — GitHub Actions runs the suite on every push, and publishes the Allure report to GitHub Pages — publicly viewable by anyone, no login required.

---

## Tech Stack

| Purpose | Tool |
| :--- | :--- |
| **Browser automation** | [Playwright](https://playwright.dev/python/) |
| **Test runner** | pytest |
| **Parallelization** | pytest-xdist |
| **Reporting** | Allure Report |
| **Retry on flake** | pytest-rerunfailures |
| **CI/CD** | GitHub Actions → GitHub Pages |

---

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml              # CI pipeline: test → report → publish
├── pages/                      # Page Object classes
├── tests/                      # Test modules (plain pytest functions)
├── page_registry.py            # Central registry wiring pages to the `pages`/`authenticated_pages` fixtures
├── utilities/
│   ├── load_json_test_data.py  # Test data loader
│   └── api_client.py           # Pre-flight API reachability check
├── auth/                       # Generated storage_state JSON files (gitignored)
├── test_data.json              # Shared test data
├── conftest.py                 # Fixtures, Allure hooks, storage_state wiring
├── pytest.ini                  # Pytest & plugin configuration
├── requirements.txt
└── .gitignore
```

---

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js (only needed locally if you want the Allure CLI to view reports)

### Install

```bash
pip install -r requirements.txt
playwright install
```

### Run the suite

```bash
pytest
```

`pytest.ini` already wires up parallel execution, both browsers, retries, screenshots, videos, tracing, and Allure result collection — no extra flags needed.

### Run only a subset

```bash
pytest -m smoke          # fast, high-value checks only
pytest -m regression     # full regression coverage
pytest -m negative       # negative/invalid-input scenarios
```

### View the Allure report locally

```bash
allure serve allure-results
```

---

## How It Works

<details>
<summary><b>Cross-browser + parallel, configured once</b></summary>

<br>

```ini
addopts = --browser chromium --browser firefox -s --screenshot=on --video=on --tracing=retain-on-failure -W ignore::DeprecationWarning -n auto --alluredir=allure-results --clean-alluredir --reruns 1 --reruns-delay 3
```

- `--browser chromium --browser firefox` → every test is parametrized across both browsers.
- `-n auto` → tests distribute across all available CPU cores.
- `--screenshot=on --video=on --tracing=retain-on-failure` → full visual evidence for every run, plus a Playwright trace (DOM snapshots, network, console) specifically retained on failures for deep debugging.
- `--reruns 1 --reruns-delay 3` → one automatic retry before a failure is final.

A `_multi_browser` fixture in `conftest.py` works around a known `pytest-playwright` limitation so cross-browser parametrization keeps working even with this project's custom fixtures wrapping `page`/`browser`.

</details>

<details>
<summary id="authenticated-session-reuse"><b>Authenticated session reuse</b></summary>

<br>

Rather than driving the login UI at the start of every single test, `conftest.py` logs in **once per browser per worker process**:

```python
@pytest.fixture(scope="session")
def standard_user_storage_state(browser, browser_name, test_data, base_url) -> str:
    ...
    context.storage_state(path=str(storage_state_path))
```

Every test that needs to be logged in (but isn't itself testing login) depends on `authenticated_pages` instead, which spins up a fresh browser context seeded from that saved state:

```python
@pytest.fixture(scope="function")
def authenticated_page(browser, standard_user_storage_state) -> Page:
    context = browser.new_context(storage_state=standard_user_storage_state)
    ...
```

Only the login/logout tests use the plain `pages` fixture (a fresh, unauthenticated page), since they need to exercise the login flow itself.

</details>

<details>
<summary><b>API-level pre-flight check</b></summary>

<br>

SauceDemo has no real backend API — product, cart, and checkout data all live inside its JS bundle rather than behind REST endpoints, so there isn't a genuine data-seeding API to call here the way there might be on an app with an actual backend. The one legitimate API-level use in this suite is a fast reachability check, using Playwright's `APIRequestContext` directly (no browser involved):

```python
@pytest.fixture(scope="session", autouse=True)
def verify_site_reachable_before_suite(api_request_context, base_url):
    verify_site_is_reachable(api_request_context, base_url)
```

If the site itself is down, the whole suite fails in milliseconds with one clear message instead of every UI test individually timing out.

</details>

<details>
<summary><b>Screenshots & videos → attached to Allure automatically</b></summary>

<br>

`conftest.py` hooks into `pytest_runtest_teardown` to locate each test's Playwright output folder and attach every `.png`/`.webm` file directly onto that test's Allure entry — reviewable inline, no digging through raw output folders.

</details>

<details>
<summary><b>CI/CD pipeline - Github Actions</b></summary>

<br>

This project uses **[GitHub Actions](https://github.com/features/actions)** for CI/CD, configured in `.github/workflows/ci.yml`. It runs automatically on every push:

1. Install dependencies (Python packages, Playwright browsers, Node.js for the Allure CLI)
2. Run the full suite (failures don't block the pipeline — reporting always completes)
3. Pull prior Allure history from `gh-pages` (for trend graphs across runs)
4. Generate the Allure report
5. Publish it to the `gh-pages` branch via the built-in `GITHUB_TOKEN` — no manual SSH deploy key setup required, unlike a self-hosted CI server
6. Explicitly fail the workflow at the end if tests failed, so GitHub still shows a red ✗ even though reporting succeeded

📋 **[View all pipeline runs and build summaries here →](https://github.com/ruby-leo/p3-saucedemo-playwright-pytest-automation/actions)**

</details>

---

## Allure Reporting

You can view the latest automated test execution results directly in the browser:
👉 **[Click Here to View Live Allure Report](https://ruby-leo.github.io/p3-saucedemo-playwright-pytest-automation/)**

Every test run — locally or in CI — produces a full **Allure Report**, giving each test its own detailed entry with pass/fail status, execution time, browser tag, and a complete visual trail of what happened.

### Screenshots & videos, per test

Thanks to `pytest.ini`'s `--screenshot=on --video=on` flags, Playwright captures a screenshot and a video for **every single test**, not just failures. `conftest.py`'s `pytest_runtest_teardown` hook then locates each test's output folder and attaches those files directly onto that test's Allure entry:

- **Screenshots** — a final-state `.png` for every test, so you can visually confirm what the page looked like at the end of the run without re-running anything.
- **Videos** — a full `.webm` recording of the entire test, useful for watching exactly what Playwright did step-by-step, especially handy for diagnosing flaky or timing-related failures (like the sort/reset tests hitting a Firefox-only race).
- **Traces** — retained only `on-failure` (`--tracing=retain-on-failure`) rather than for every test, since traces are heavier; each is a `.zip` containing DOM snapshots, network activity, and console logs, downloadable straight from the Allure entry and viewable via `npx playwright show-trace <file>` or at [trace.playwright.dev](https://trace.playwright.dev/).

The `test_checkout.py` order-confirmation test goes one step further and manually attaches an extra mid-flow screenshot (the order summary, right before finalizing) via `allure.attach()`, on top of the automatic end-of-test capture.

### Browser tagging

A `_tag_browser_in_allure` fixture tags every result with its browser (`chromium` / `firefox`), so the report's **Tags** filter lets you isolate results per browser instead of digging through a flat list.

### Trend history across runs

In CI, the pipeline pulls the previous report's `history/` folder from `gh-pages` before generating a new one, so the published report shows trend graphs (pass/fail rate, duration) across runs over time — not just a snapshot of the latest run.

### Viewing the report

- **Locally:** `allure serve allure-results` (see [Getting Started](#getting-started))
- **From CI:** published automatically to GitHub Pages after every run — [![Allure Report](https://img.shields.io/badge/Allure-Report-orange?logo=testcafe)](https://ruby-leo.github.io/p3-saucedemo-playwright-pytest-automation/)

---

## Test Coverage

| Test Module | Covers |
| :--- | :--- |
| `test_login.py` | TC-1: login across all six predefined SauceDemo users (including the locked-out case). TC-2: invalid credential combinations and their error messages. |
| `test_logout_and_cart_visibility.py` | TC-3: logout redirects back to the login screen. TC-4: cart icon visibility post-login. |
| `test_cart_flow.py` | TC-5, TC-6, TC-7 (combined — see the module docstring for why): random product selection, adding to cart, and verifying cart contents match exactly. |
| `test_checkout.py` | TC-8: full checkout flow with a known product set, order summary verification, screenshot capture, and order confirmation. |
| `test_sorting.py` | TC-9: all four sort options (name/price, ascending/descending). |
| `test_reset_app_state.py` | TC-10: Reset App State clears the cart back to empty. |

---

## OOP Principles in This Project

The suite is built around the **Page Object Model**, which draws mainly on three of the four core OOP principles:

- **Encapsulation** — Each page class hides its own locators and DOM details behind methods. Tests never touch a CSS selector directly — e.g. `inventory.add_product_to_cart("Sauce Labs Backpack")` hides the `.inventory_item` locator, the `filter(has_text=...)` scoping, and the button role query inside `InventoryPage`. If SauceDemo's markup changes, only the page object needs updating.

- **Abstraction** — Methods expose *what* a test wants to do, not *how* it's done on the page. `login()`, `fill_checkout_information()`, `sort_by()`, and `reset_app_state()` each collapse multiple low-level interactions into one call that reads like a business step rather than a UI script.

- **Inheritance** — Every page object (`LoginPage`, `InventoryPage`, `CartPage`, `CheckoutPage`) inherits from `BasePage`, which holds the shared `page` handle and the common `navigate_to()` method. Shared behavior lives once in the parent; each subclass adds only what's specific to its own screen.

**Where it lives in the codebase:**

| Principle | Where |
| :--- | :--- |
| **Inheritance** | `base_page.py` (parent) → `login_page.py`, `inventory_page.py`, `cart_page.py`, `checkout_page.py` (subclasses) |
| **Encapsulation** | Locators declared privately inside each page class's `__init__`, never exposed as raw selectors to tests |
| **Abstraction** | Higher-level methods like `fill_checkout_information()`, `add_product_to_cart()` |
