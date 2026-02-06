# Full-Stack Selenium E2E Test

This test validates the **complete application stack** from browser to database using Selenium WebDriver.

## What It Tests

### Test 1: Full Stack Submit and Chart Render
1. ✅ Starts Flask backend server on port 5000
2. ✅ Serves built React frontend
3. ✅ Opens Chrome/Chromium browser
4. ✅ Loads the application
5. ✅ Verifies form has default values (dates, inflation, stocks, etc.)
6. ✅ Clicks the "Submit" button
7. ✅ Waits for backend API call to complete
8. ✅ Validates Plotly chart renders with data
9. ✅ Captures screenshots (before and after)
10. ✅ Verifies no error messages displayed

### Test 2: Chart Interactive Elements
1. ✅ Validates chart has Plotly modebar (zoom, pan controls)
2. ✅ Validates chart has legend
3. ✅ Validates chart has axis tick marks
4. ✅ Verifies interactive chart structure

## Requirements

### System Requirements
- **Chrome** or **Chromium** browser installed
- **ChromeDriver** (auto-managed by Selenium 4.6+)
- **Node.js** (for frontend build)
- **Python 3.14+**

### Install Chrome/Chromium

**Ubuntu/Debian:**
```bash
# Install Google Chrome (recommended for containers)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get install ./google-chrome-stable_current_amd64.deb

# Or use chromium if available
sudo apt update
sudo apt install chromium-browser  # May require snap on Ubuntu 24.04+
```

**macOS:**
```bash
brew install chromium --no-quarantine
```

**Windows:**
Download from https://www.google.com/chrome/

### Install Python Dependencies
```bash
pip install -r requirements.txt
```

## Running the Tests

### Step 1: Build Frontend
```bash
cd ../frontend
npm install  # If not already done
npm run build
cd ../backend
```

### Step 2: Run Selenium Tests
```bash
# Run with visible output (recommended)
pytest test_selenium_e2e.py -v -s

# Run with screenshot verification
pytest test_selenium_e2e.py -v -s
# Screenshots saved to: backend/screenshots/
```

## Test Output Example

```
🚀 Starting Flask backend server...
✓ Backend server ready on http://localhost:5000

📦 Building React frontend...
✓ Frontend build directory already exists

🌐 Setting up Chrome WebDriver...
✓ Chrome WebDriver initialized

================================================================
🧪 Starting Full-Stack Selenium E2E Test
================================================================

📄 Loading application...
✓ Application loaded successfully

📋 Verifying form elements...
  Start Date: 2022-01-10
  End Date: 2026-01-10
  Predicted Inflation: 1.03
✓ Form has default values

🖱️  Finding Submit button...
✓ Submit button found
✓ Screenshot saved: backend/screenshots/before_submit.png

🚀 Clicking Submit button...
✓ Submit button clicked

⏳ Waiting for chart to render...
✓ Plotly chart container found

📊 Validating chart content...
✓ Found 1 SVG element(s) in chart
✓ Found 6 data trace(s) in chart
✓ Final screenshot saved: backend/screenshots/after_submit_with_chart.png
✓ Chart size: 1200x600px
✓ No error messages displayed

================================================================
✅ Full-Stack E2E Test PASSED
================================================================

📸 Screenshots saved in: backend/screenshots
  - Before submit: before_submit.png
  - After submit: after_submit_with_chart.png
```

## Screenshots

The test automatically captures screenshots at key points:

```
backend/screenshots/
├── before_submit.png              # Form with default values
├── after_submit_with_chart.png    # Rendered Plotly chart
└── chart_render_failed.png        # Only created if test fails
```

These screenshots are useful for:
- Visual regression testing
- Debugging test failures
- Documentation
- Verification of UI changes

## Troubleshooting

### Chrome/Chromium Not Found
```
RuntimeError: Chrome/Chromium is required for Selenium tests but not available.
Install with: sudo apt-get install google-chrome-stable

Solution: Install Google Chrome or Chromium (see Requirements section)
```

**Note:** The test will **FAIL** (not skip) if Chrome is not available. This is intentional to ensure browser testing is properly configured in CI/CD environments.

### Frontend Not Built
```
Error: Frontend build failed
Solution: cd ../frontend && npm install && npm run build
```

### Port 5000 Already In Use
```
Error: Backend server failed to start
Solution: Kill process on port 5000
  lsof -ti:5000 | xargs kill -9
```

### Chart Doesn't Render
- Check network connectivity (test needs real yfinance + BLS APIs)
- Verify backend can fetch stock data: `curl http://localhost:5000/api/v1.0/plot/`
- Check browser console: Screenshots will capture any JS errors

### Slow Tests
The Selenium tests are intentionally slow because they:
- Build frontend (~30-60s)
- Start real backend server (~2-5s)
- Make real API calls to yfinance and BLS (~5-10s)
- Render complex Plotly charts (~2-3s)

Total time: ~45-90 seconds per test

## Skipping Selenium Tests

If you don't have Chrome installed or want faster test runs:

```bash
# Run all tests except Selenium
pytest -m "not selenium"

# This runs only unit tests + E2E API tests
pytest test_app.py test_e2e.py
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Install Chrome
  run: |
    sudo apt-get update
    sudo apt-get install chromium-browser

- name: Build Frontend
  run: |
    cd frontend
    npm ci
    npm run build

- name: Run Selenium Tests
  run: |
    cd backend
    pytest test_selenium_e2e.py -v
```

### Docker
Use an image with Chrome pre-installed:
```dockerfile
FROM selenium/standalone-chrome:latest
# ... rest of your Dockerfile
```

## What This Tests That Unit Tests Don't

| Aspect | Unit/E2E API Tests | Selenium Tests |
|--------|-------------------|----------------|
| Backend logic | ✅ | ✅ |
| API endpoints | ✅ | ✅ |
| Frontend rendering | ❌ | ✅ |
| User interactions | ❌ | ✅ |
| Chart visualization | ❌ | ✅ |
| Browser compatibility | ❌ | ✅ |
| JavaScript execution | ❌ | ✅ |
| CSS layout | ❌ | ✅ |
| Full request/response cycle | ❌ | ✅ |

## Performance

- **Unit tests (test_app.py)**: ~1.5 seconds ⚡
- **E2E API tests (test_e2e.py)**: ~20 seconds 🚀
- **Selenium tests (test_selenium_e2e.py)**: ~60 seconds 🐢

Use Selenium tests sparingly - they're expensive but comprehensive.
