# conftest.py
import logging
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Page, expect

from page_registry import PageRegistry
from pages.login_page import LoginPage
from utilities.load_json_test_data import read_json
from utilities.api_client import verify_site_is_reachable

# Set a moderate global assertion timeout - SauceDemo is a lightweight demo
# app, so this is mostly a safety margin for CI runners under load.
expect.set_options(timeout=10000)

AUTH_DIR = Path(__file__).resolve().parent / "auth"
AUTH_DIR.mkdir(exist_ok=True)


# ============================================================
# base_url fallback
# ============================================================
@pytest.fixture(scope="session")
def base_url(base_url, request):
    """pytest-playwright's own `base_url` fixture only reflects a --base-url
    CLI flag - it returns None if the project instead configures base_url
    via pytest.ini (as this project does), even though pytest's terminal
    header display checks both and can misleadingly show the right value.
    Falls back to the ini setting so every fixture/test using `base_url`
    gets a real value either way."""
    return base_url or request.config.getini("base_url")


# ============================================================
# Test data
# ============================================================
@pytest.fixture(scope="session")
def test_data():
    return read_json("test_data.json")


# ============================================================
# Pre-flight API check (Playwright APIRequestContext)
# ============================================================
@pytest.fixture(scope="session")
def api_request_context(playwright, base_url):
    """Session-scoped APIRequestContext, independent of any browser - used
    purely for the pre-flight reachability check below."""
    context = playwright.request.new_context(base_url=base_url)
    yield context
    context.dispose()


@pytest.fixture(scope="session", autouse=True)
def verify_site_reachable_before_suite(api_request_context, base_url):
    """Runs once per session (per xdist worker) before any browser-based
    test executes. Fails fast with a clear message if the site itself is
    unreachable, instead of every UI test individually timing out."""
    verify_site_is_reachable(api_request_context, base_url)


# ============================================================
# Multi-browser parametrization safeguard
# ============================================================
@pytest.fixture(autouse=True)
def _multi_browser(browser_name):
    """Ensures pytest-playwright correctly parametrizes every test across
    all --browser values in pytest.ini, even though this suite defines its
    own fixtures that wrap `page`/`browser` (see
    microsoft/playwright-pytest#172 - custom fixtures wrapping `page`
    without depending on `browser_name` can otherwise silently break
    cross-browser parametrization)."""
    return browser_name


# ============================================================
# Authenticated session reuse via storage_state
# ============================================================
@pytest.fixture(scope="session")
def standard_user_storage_state(browser, browser_name, test_data, base_url) -> str:
    """Logs in once as standard_user via the UI, saves the authenticated
    session (cookies + localStorage) to a JSON file, and returns its path.

    Session-scoped per browser, per xdist worker: under `-n auto`, each
    worker process performs this login exactly once per browser rather than
    once per test - a large reduction versus re-logging-in before every
    single test, without needing cross-process coordination.
    """
    storage_state_path = AUTH_DIR / f"storage_state_{browser_name}.json"

    context = browser.new_context()
    page = context.new_page()
    page.goto(base_url)

    login_page = LoginPage(page)
    credentials = test_data["users"]["standard_user"]
    login_page.login(credentials["username"], credentials["password"])
    page.wait_for_url("**/inventory.html")

    context.storage_state(path=str(storage_state_path))
    context.close()

    logging.info(f"Saved authenticated storage state for {browser_name} -> {storage_state_path}")
    return str(storage_state_path)


@pytest.fixture(scope="function")
def browser_context_args(browser_context_args, request, standard_user_storage_state):
    """Merges the saved storage_state into the SAME context-args dict that
    pytest-playwright itself uses to build its `context`/`page` fixtures,
    whenever a test is marked @pytest.mark.authenticated.

    This is deliberately NOT done by manually calling browser.new_context()
    in a custom fixture. pytest-playwright's automatic screenshot/video/
    trace capture only instruments contexts created through its OWN
    context/page fixture chain (see microsoft/playwright-pytest#139) - a
    manually-created context is invisible to that mechanism, silently
    losing all three artifact types. Routing storage_state through
    browser_context_args instead means the authenticated page is still
    "pytest-playwright's own" context under the hood, so --screenshot=on,
    --video=on, and --tracing=retain-on-failure all keep working exactly
    as they do for any other test.
    """
    if request.node.get_closest_marker("authenticated"):
        return {**browser_context_args, "storage_state": standard_user_storage_state}
    return browser_context_args


@pytest.fixture(scope="function")
def pages(page: Page, request, base_url) -> PageRegistry:
    """PageRegistry wrapping the current page. Pre-authenticated as
    standard_user when the test carries @pytest.mark.authenticated (via the
    browser_context_args override above); otherwise a fresh, unauthenticated
    page - used by the login/logout tests that need to exercise that flow
    directly."""
    registry = PageRegistry(page)
    if request.node.get_closest_marker("authenticated"):
        registry.inventory_page.navigate_to(f"{base_url}/inventory.html")
        registry.inventory_page.page_title.wait_for(state="visible")
    return registry


# ============================================================
# Allure: tag every result with its browser
# ============================================================
@pytest.fixture(autouse=True)
def _tag_browser_in_allure(browser_name):
    """Tags every Allure result with its browser, so the report's Tags
    filter can isolate chromium-only or firefox-only results."""
    allure.dynamic.tag(browser_name)


# ============================================================
# Allure: environment info panel
# ============================================================
def pytest_sessionstart(session):
    """Writes Allure's environment.properties file once per session, so the
    generated report's Overview > Environment panel shows exactly what was
    tested (base URL, browsers, framework) without digging through logs."""
    try:
        results_dir = Path(session.config.getoption("--alluredir") or "allure-results")
        results_dir.mkdir(parents=True, exist_ok=True)
        base_url = session.config.getini("base_url")
        env_file = results_dir / "environment.properties"
        with open(env_file, "w") as f:
            f.write(f"Base_URL={base_url}\n")
            f.write("Browsers=chromium, firefox\n")
            f.write("Framework=Playwright + pytest (no BDD)\n")
    except Exception as e:
        logging.warning(f"Could not write Allure environment.properties: {e}")


# ============================================================
# Attach screenshots & videos to Allure automatically
# ============================================================
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item, nextitem):
    yield
    try:
        base_dir = item.config.getoption("--output", default="test-results")
        base_path = Path(base_dir)
        if not base_path.is_dir():
            return

        node_id_slug = (
            item.name.replace("_", "-").replace("@", "-").replace(" ", "-")
            .replace("[", "-").replace("]", "").replace("...", "-")
            .replace(".", "-").replace("---", "-").replace("--", "-").lower()
        )

        specific_test_dir = None
        for folder in base_path.iterdir():
            if folder.is_dir() and node_id_slug in folder.name:
                specific_test_dir = folder
                break

        if specific_test_dir:
            for file in specific_test_dir.iterdir():
                if file.is_file():
                    if file.suffix == ".png":
                        allure.attach.file(
                            str(file), name=file.name,
                            attachment_type=allure.attachment_type.PNG,
                        )
                    elif file.suffix == ".webm":
                        allure.attach.file(
                            str(file), name=file.name,
                            attachment_type=allure.attachment_type.WEBM,
                        )
                    elif file.suffix == ".zip":
                        # Playwright trace file (from --tracing=retain-on-failure) -
                        # only present for tests that failed, since traces are
                        # heavy and this project only retains them on failure.
                        # allure-python-commons has no ZIP/trace attachment_type
                        # (unlike its JS counterpart), so extension="zip" is used
                        # instead - Allure still serves it as a downloadable file;
                        # open it locally via `npx playwright show-trace <file>`
                        # or by dragging it into https://trace.playwright.dev/
                        allure.attach.file(
                            str(file), name=file.name, extension="zip",
                        )
    except Exception as e:
        logging.error(f"Error attaching screenshot/video: {e}")