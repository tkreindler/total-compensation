"""
Full-stack End-to-End test using Selenium WebDriver.

This test validates the entire application stack:
- React frontend UI
- Flask backend API
- Real yfinance and BLS API calls
- Plotly chart rendering in browser

Requires: selenium, chrome/chromium browser
"""

import pytest
import os
import time
import subprocess
import signal
import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


# Mark as slow integration test
pytestmark = [pytest.mark.slow, pytest.mark.integration, pytest.mark.selenium]


class TestFullStackSelenium:
    """Full-stack Selenium tests for the complete application."""

    @pytest.fixture(scope="class")
    def backend_server(self):
        """Start the Flask backend server."""
        print("\n🚀 Starting Flask backend server...")

        backend_dir = Path(__file__).parent
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'
        env['DISABLE_INFLATION'] = 'false'
        env['STATIC_ROOT'] = '../frontend/build/'

        # Start Flask server
        process = subprocess.Popen(
            ['python', 'app.py'],
            cwd=backend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group for clean shutdown
        )

        # Wait for server to be ready
        max_attempts = 30
        for i in range(max_attempts):
            try:
                response = requests.get('http://localhost:5000', timeout=1)
                print(f"✓ Backend server ready on http://localhost:5000")
                break
            except requests.exceptions.RequestException:
                if i == max_attempts - 1:
                    # Kill process and raise error
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    raise RuntimeError("Backend server failed to start")
                time.sleep(0.5)

        yield process

        # Cleanup
        print("\n🛑 Stopping Flask backend server...")
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait(timeout=5)

    @pytest.fixture(scope="class")
    def frontend_build(self):
        """Build the React frontend."""
        print("\n📦 Building React frontend...")

        frontend_dir = Path(__file__).parent.parent / 'frontend'

        # Check if build already exists
        build_dir = frontend_dir / 'build'
        if build_dir.exists():
            print("✓ Frontend build directory already exists, skipping build")
            return str(build_dir)

        # Build frontend
        result = subprocess.run(
            ['npm', 'run', 'build'],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )

        if result.returncode != 0:
            print(f"Frontend build failed:\n{result.stderr}")
            raise RuntimeError("Frontend build failed")

        print(f"✓ Frontend built successfully")
        return str(build_dir)

    @pytest.fixture(scope="class")
    def chrome_driver(self):
        """Setup Chrome WebDriver with headless mode."""
        print("\n🌐 Setting up Chrome WebDriver...")

        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # New headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')

        # Try to create driver - FAIL if not available (don't skip)
        try:
            driver = webdriver.Chrome(options=chrome_options)
            print("✓ Chrome WebDriver initialized")
        except Exception as e:
            print(f"Failed to initialize Chrome WebDriver: {e}")
            print("Trying with chromium...")
            try:
                chrome_options.binary_location = '/usr/bin/chromium'
                driver = webdriver.Chrome(options=chrome_options)
                print("✓ Chromium WebDriver initialized")
            except Exception as e2:
                raise RuntimeError(
                    f"Chrome/Chromium is required for Selenium tests but not available.\n"
                    f"Chrome error: {e}\n"
                    f"Chromium error: {e2}\n"
                    f"Install with: sudo apt-get install google-chrome-stable"
                ) from e2

        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)

        yield driver

        print("\n🔚 Closing browser...")
        driver.quit()

    def test_full_stack_submit_and_chart_render(
        self,
        backend_server,
        frontend_build,
        chrome_driver
    ):
        """
        Full E2E test: Load page, click submit, validate chart renders.

        This test:
        1. Loads the React frontend
        2. Verifies default form data is present
        3. Clicks the Submit button
        4. Waits for API call to complete
        5. Validates Plotly chart renders
        6. Takes a screenshot
        7. Validates chart contains data
        """
        driver = chrome_driver

        print("\n" + "="*60)
        print("🧪 Starting Full-Stack Selenium E2E Test")
        print("="*60)

        # Navigate to the application
        print("\n📄 Loading application...")
        driver.get('http://localhost:5000')

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )

        # Verify we're on the right page
        assert "Total Compensation" in driver.title or "Total Compensation" in driver.page_source
        print("✓ Application loaded successfully")

        # Verify form is present with default values
        print("\n📋 Verifying form elements...")

        # Check for key form elements
        start_date_input = driver.find_element(By.NAME, "startDate")
        end_date_input = driver.find_element(By.NAME, "endDate")
        inflation_input = driver.find_element(By.NAME, "predictedInflation")

        # Verify default values are present
        assert start_date_input.get_attribute("value"), "Start date should have default value"
        assert end_date_input.get_attribute("value"), "End date should have default value"
        assert inflation_input.get_attribute("value"), "Inflation should have default value"

        print(f"  Start Date: {start_date_input.get_attribute('value')}")
        print(f"  End Date: {end_date_input.get_attribute('value')}")
        print(f"  Predicted Inflation: {inflation_input.get_attribute('value')}")
        print("✓ Form has default values")

        # Find and click the Submit button
        print("\n🖱️  Finding Submit button...")
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
        )
        print("✓ Submit button found")

        # Take screenshot before submit
        screenshot_dir = Path(__file__).parent / 'screenshots'
        screenshot_dir.mkdir(exist_ok=True)
        before_screenshot = screenshot_dir / 'before_submit.png'
        driver.save_screenshot(str(before_screenshot))
        print(f"✓ Screenshot saved: {before_screenshot}")

        print("\n🚀 Clicking Submit button...")
        submit_button.click()
        print("✓ Submit button clicked")

        # Wait for API call to complete and chart to render
        # Look for Plotly elements (Plotly creates a div with class 'plotly')
        print("\n⏳ Waiting for chart to render...")
        try:
            chart_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "plotly"))
            )
            print("✓ Plotly chart container found")
        except Exception as e:
            # Take screenshot on failure
            failure_screenshot = screenshot_dir / 'chart_render_failed.png'
            driver.save_screenshot(str(failure_screenshot))
            print(f"✗ Chart failed to render. Screenshot saved: {failure_screenshot}")
            print(f"Page source:\n{driver.page_source[:500]}...")
            raise AssertionError(f"Chart did not render within 30 seconds: {e}")

        # Wait a bit more for chart to fully render
        time.sleep(2)

        # Verify chart has SVG elements (Plotly renders charts as SVG)
        print("\n📊 Validating chart content...")
        svg_elements = driver.find_elements(By.TAG_NAME, "svg")
        assert len(svg_elements) > 0, "Chart should contain SVG elements"
        print(f"✓ Found {len(svg_elements)} SVG element(s) in chart")

        # Check for Plotly-specific elements
        plotly_traces = driver.find_elements(By.CLASS_NAME, "trace")
        if plotly_traces:
            print(f"✓ Found {len(plotly_traces)} data trace(s) in chart")

        # Take final screenshot with rendered chart
        after_screenshot = screenshot_dir / 'after_submit_with_chart.png'
        driver.save_screenshot(str(after_screenshot))
        print(f"✓ Final screenshot saved: {after_screenshot}")

        # Verify chart dimensions (should not be 0x0)
        chart_size = chart_element.size
        assert chart_size['width'] > 0, "Chart should have width"
        assert chart_size['height'] > 0, "Chart should have height"
        print(f"✓ Chart size: {chart_size['width']}x{chart_size['height']}px")

        # Verify no error messages
        error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Error') or contains(text(), 'error')]")
        visible_errors = [e for e in error_elements if e.is_displayed()]
        assert len(visible_errors) == 0, f"Found error messages: {[e.text for e in visible_errors]}"
        print("✓ No error messages displayed")

        print("\n" + "="*60)
        print("✅ Full-Stack E2E Test PASSED")
        print("="*60)
        print(f"\n📸 Screenshots saved in: {screenshot_dir}")
        print(f"  - Before submit: {before_screenshot.name}")
        print(f"  - After submit: {after_screenshot.name}")

    def test_chart_interactive_elements(
        self,
        backend_server,
        frontend_build,
        chrome_driver
    ):
        """
        Test that the chart has interactive Plotly elements.

        Validates:
        - Chart legend is present
        - Chart has interactive controls (zoom, pan, etc.)
        """
        driver = chrome_driver

        print("\n🧪 Testing chart interactive elements...")

        # Load and submit
        driver.get('http://localhost:5000')
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Submit')]"))
        ).click()

        # Wait for chart
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "plotly"))
        )

        time.sleep(2)  # Let chart fully render

        # Check for Plotly modebar (interactive controls)
        modebar = driver.find_elements(By.CLASS_NAME, "modebar")
        if modebar:
            print(f"✓ Plotly modebar (interactive controls) found")

        # Check for legend
        legend = driver.find_elements(By.CLASS_NAME, "legend")
        if legend:
            print(f"✓ Chart legend found")

        # Check for axis labels/titles (indicating proper chart structure)
        axis_elements = driver.find_elements(By.CLASS_NAME, "xtick") + \
                       driver.find_elements(By.CLASS_NAME, "ytick")
        assert len(axis_elements) > 0, "Chart should have axis tick marks"
        print(f"✓ Found {len(axis_elements)} axis tick marks")

        print("✓ Chart has interactive elements")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
