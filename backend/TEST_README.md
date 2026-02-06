# Backend Test Suite

This directory contains comprehensive testing for the Total Compensation backend API with two test suites:

## Test Suites

### 1. Unit Tests (`test_app.py`) - 22 tests
Fast unit tests with mocked dependencies for rapid development feedback.

### 2. End-to-End Functional Tests (`test_e2e.py`) - 18 tests
Slow integration tests that make real API calls to validate actual system behavior.

## Test Coverage

### Unit Tests (`test_app.py`)

The unit test suite includes **22 tests** covering:

### Core Business Logic
- **Base Pay Calculations** - Single entries, multiple raises/promotions, edge cases
- **Annual Bonus Calculations** - Default multipliers, past performance bonuses
- **Signing Bonus Calculations** - Amortization over time periods
- **Stock Award Calculations** - RSU grants with historical and predicted prices
- **CPI Inflation Adjustments** - Integration with Bureau of Labor Statistics API

### Data Series Generation
- Base salary series over time
- Annual bonus series with variable multipliers
- Signing bonus amortization
- Stock compensation with price tracking
- Total compensation aggregation
- Inflation-adjusted starting pay

### API Endpoints
- POST `/api/v1.0/plot/` - Main plotting endpoint
- Content-Type validation
- Multiple stock grants handling
- Error handling

### Edge Cases & Data Consistency
- Empty pay arrays
- Zero-duration bonuses
- Future stock price predictions
- Date alignment across series
- Aggregation correctness

### End-to-End Functional Tests (`test_e2e.py`)

The E2E test suite includes **18 tests** covering:

- **Real Yahoo Finance API Integration** - Actual stock price fetching (MSFT, AAPL, GOOGL, TSLA)
- **Real BLS CPI API Integration** - Actual inflation data fetching
- **Full API Stack Testing** - Complete Flask app with real dependencies
- **Real-World Compensation Scenarios** - Microsoft-style comp, multi-year vesting, overlapping grants
- **API Resilience Testing** - Invalid tickers, future dates, error handling

**Note:** E2E tests require network connectivity and are slower (~30-60 seconds total).

## Running Tests

### Run Only Fast Unit Tests (Recommended for Development)
```bash
cd backend
pytest test_app.py
```

### Run Only E2E Tests (Real API Calls)
```bash
pytest test_e2e.py -v
```

### Run All Tests
```bash
pytest
```

### Skip Slow Tests (Unit Tests Only)
```bash
pytest -m "not slow"
```

### Run Only Integration/E2E Tests
```bash
pytest -m integration
```

### Run Specific Test Class
```bash
pytest test_app.py::TestBasePay -v
pytest test_e2e.py::TestRealYFinanceIntegration -v
```

### Run Specific Test
```bash
pytest test_app.py::TestBasePay::test_get_base_pay_single_entry -v
pytest test_e2e.py::TestRealYFinanceIntegration::test_yfinance_ticker_fetch -v
```

### Run with Coverage Report
```bash
pip install pytest-cov
pytest test_app.py --cov=. --cov-report=html  # Unit tests only
```

### Run with Print Statements Visible
```bash
pytest -v -s  # Shows print() output for debugging
```

## Test Dependencies

The tests require the following packages (included in requirements.txt):
- `pytest==8.3.4` - Testing framework
- `pytest-mock==3.14.0` - Mocking support

## Test Structure

Tests are organized into logical classes:

```
TestBasePay          - Base salary calculation tests
TestAnnualBonus      - Annual bonus logic tests
TestSeriesGeneration - Time series generation tests
TestCPIInflation     - Inflation adjustment tests
TestAPIEndpoints     - Flask API endpoint tests
TestEdgeCases        - Edge case handling
TestDataConsistency  - Data integrity tests
```

## Mocking

The test suite mocks external dependencies to ensure fast, reliable tests:

- **yfinance API** - Stock price data is mocked to avoid network calls
- **BLS API** - CPI data is mocked for consistent test results

## Continuous Integration

These tests should be run:
- Before committing changes
- In CI/CD pipelines
- Before deploying to production

## Sample Test Data

Tests use realistic sample data including:
- Base salary: $150,000 with raises
- Signing bonus: $50,000 over 2 years
- Annual bonus: 15-20% of base
- Stock grants: 100 shares of MSFT
- Time period: 2024-2026

## Adding New Tests

When adding new features, please:
1. Add corresponding tests to `test_app.py`
2. Follow the existing test structure and naming conventions
3. Use appropriate mocking for external dependencies
4. Ensure all tests pass before committing

## Troubleshooting

### Import Errors
Make sure you're in the backend directory and have installed all dependencies:
```bash
pip install -r requirements.txt
```

### Failed Tests
Run with verbose output to see detailed error messages:
```bash
pytest -v --tb=long
```

### Environment Variables
Tests set necessary environment variables automatically. No manual configuration needed.
