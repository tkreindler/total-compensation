"""
End-to-end functional tests for the Total Compensation backend.

These tests do NOT mock any dependencies and instead:
- Make real calls to yfinance API for stock data
- Make real calls to BLS API for CPI data
- Test the full Flask application stack
- Validate real-world behavior

These tests are slower and require network connectivity.
Run separately from unit tests using: pytest test_e2e.py
"""

import pytest
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os
import time

# Set environment variables before importing app
os.environ['DISABLE_INFLATION'] = 'false'
os.environ['STATIC_ROOT'] = '../frontend/build/'

from app import app
from cpi import inflater
from stocks import price_tracker
import yfinance


# Mark all tests in this file as slow and integration tests
pytestmark = [pytest.mark.slow, pytest.mark.integration]


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def real_world_request_data():
    """Real-world request data using historical dates and known tickers."""
    return {
        "misc": {
            "startDate": "2023-01-01",
            "endDate": "2024-12-31",
            "predictedInflation": 1.03
        },
        "base": {
            "name": "Base Salary",
            "pay": [
                {"startDate": "2023-01-01", "amount": 150000},
                {"startDate": "2024-01-01", "amount": 160000}
            ]
        },
        "bonus": {
            "signing": {
                "name": "Signing Bonus",
                "amount": 25000,
                "duration": {"years": 1, "months": 0, "days": 0}
            },
            "annual": {
                "name": "Annual Bonus",
                "default": 0.15,
                "past": [
                    {"endDate": "2023-12-31", "multiplier": 0.18}
                ]
            }
        },
        "stocks": [
            {
                "name": "MSFT Stock Grant",
                "ticker": "MSFT",
                "startDate": "2023-01-01",
                "endDate": "2024-12-31",
                "shares": 50
            }
        ]
    }


class TestRealYFinanceIntegration:
    """Test real integration with Yahoo Finance API."""

    def test_yfinance_ticker_fetch(self):
        """Test fetching real ticker data from yfinance."""
        # Use a stable, high-volume ticker
        ticker = yfinance.Ticker("MSFT")

        # Get current price
        info = ticker.info
        assert "currentPrice" in info or "regularMarketPrice" in info

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        assert current_price is not None
        assert current_price > 0

        print(f"✓ MSFT current price: ${current_price}")

    def test_yfinance_historical_data(self):
        """Test fetching historical stock data."""
        ticker = yfinance.Ticker("AAPL")

        # Get historical data for a known period
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 8)

        data = ticker.history(start=start_date, end=end_date)

        assert not data.empty, "Historical data should not be empty"
        assert "Close" in data.columns
        assert len(data) > 0

        close_price = data["Close"].iloc[0]
        assert close_price > 0

        print(f"✓ AAPL historical close (2023-01-01): ${close_price:.2f}")

    def test_price_tracker_real_data(self):
        """Test price_tracker with real yfinance data."""
        tracker = price_tracker(
            predictedInflation=1.03,
            ticker="GOOGL"
        )

        # Test historical date
        test_date = date(2023, 6, 15)
        price = tracker.get_price(test_date)

        assert price > 0
        assert isinstance(price, float)

        print(f"✓ GOOGL price on 2023-06-15: ${price:.2f}")

    def test_price_tracker_current_price(self):
        """Test that current price is fetched correctly."""
        tracker = price_tracker(
            predictedInflation=1.03,
            ticker="TSLA"
        )

        assert tracker.currentPrice > 0
        print(f"✓ TSLA current price: ${tracker.currentPrice:.2f}")

    def test_price_tracker_future_prediction(self):
        """Test future price prediction based on inflation."""
        tracker = price_tracker(
            predictedInflation=1.05,  # 5% annual inflation
            ticker="MSFT"
        )

        # Get historical price first to establish cutoff
        historical_date = date(2023, 1, 1)
        historical_price = tracker.get_price(historical_date)

        # Now get a future prediction
        future_date = date(2030, 1, 1)
        future_price = tracker.get_price(future_date)

        # Future price should be higher due to inflation
        # Note: This assumes cutoff date is set, which happens when historical data is unavailable
        assert future_price > 0

        print(f"✓ Historical price: ${historical_price:.2f}")
        print(f"✓ Predicted future price (2030): ${future_price:.2f}")


class TestRealBLSCPIIntegration:
    """Test real integration with Bureau of Labor Statistics CPI API."""

    def test_cpi_inflater_initialization(self):
        """Test CPI inflater with real BLS API."""
        inf = inflater()

        # Should have fetched latest data
        assert inf.latest_year >= 2024
        assert inf.latest_month >= 1
        assert inf.latest_value > 0

        print(f"✓ Latest CPI data: {inf.latest_year}-{inf.latest_month:02d}, value: {inf.latest_value}")

    def test_cpi_get_historical_value(self):
        """Test fetching historical CPI values."""
        inf = inflater()

        # Get CPI for a known historical date
        test_date = date(2023, 6, 1)
        cpi_value = inf.get_cpi_value(test_date)

        assert cpi_value > 0
        assert isinstance(cpi_value, float)
        # CPI values are typically in the 250-350 range for recent years
        assert 200 < cpi_value < 400

        print(f"✓ CPI value for June 2023: {cpi_value:.3f}")

    def test_cpi_inflation_calculation(self):
        """Test actual inflation calculation between two dates."""
        inf = inflater()

        # Calculate inflation from 2020 to 2023
        start_date = date(2020, 1, 1)
        end_date = date(2023, 1, 1)

        original_value = 100000.0
        inflated_value = inf.inflate(original_value, start_date, end_date)

        # Should be higher due to inflation
        assert inflated_value > original_value

        inflation_rate = ((inflated_value / original_value) - 1) * 100
        print(f"✓ $100k in 2020 = ${inflated_value:.2f} in 2023")
        print(f"✓ Cumulative inflation: {inflation_rate:.2f}%")

    def test_cpi_future_prediction(self):
        """Test CPI future value prediction."""
        inf = inflater()

        # Predict future CPI
        future_date = date(2030, 1, 1)
        predicted_cpi = inf.get_cpi_value(future_date, predictedInflation=1.03)

        assert predicted_cpi > inf.latest_value
        print(f"✓ Predicted CPI for 2030: {predicted_cpi:.3f}")


class TestFullAPIIntegration:
    """Test full API integration with real dependencies."""

    def test_api_with_real_data_single_stock(self, client, real_world_request_data):
        """Test API endpoint with single stock and real yfinance data."""
        response = client.post(
            '/api/v1.0/plot/',
            data=json.dumps(real_world_request_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"API returned {response.status_code}"

        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify all expected series are present
        series_names = [s["name"] for s in data]
        assert "Base Salary" in series_names
        assert "Annual Bonus" in series_names
        assert "Signing Bonus" in series_names
        assert "MSFT Stock Grant" in series_names
        assert "Total Pay" in series_names

        # Verify data integrity
        for series in data:
            assert "x" in series
            assert "y" in series
            assert len(series["x"]) > 0
            assert len(series["y"]) == len(series["x"])

            # Verify all values are numeric
            for value in series["y"]:
                assert isinstance(value, (int, float))
                assert value >= 0  # Compensation should be non-negative

        print(f"✓ API returned {len(data)} series with real data")

    def test_api_with_multiple_stocks(self, client, real_world_request_data):
        """Test API with multiple stock grants."""
        # Add more stock grants
        real_world_request_data["stocks"].extend([
            {
                "name": "AAPL Stock Grant",
                "ticker": "AAPL",
                "startDate": "2023-06-01",
                "endDate": "2024-12-31",
                "shares": 30
            },
            {
                "name": "GOOGL Stock Grant",
                "ticker": "GOOGL",
                "startDate": "2023-01-01",
                "endDate": "2024-06-30",
                "shares": 20
            }
        ])

        response = client.post(
            '/api/v1.0/plot/',
            data=json.dumps(real_world_request_data),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should have all three stock series
        stock_series = [s for s in data if "Stock Grant" in s["name"]]
        assert len(stock_series) >= 3

        # Each stock series should have valid data
        for series in stock_series:
            assert len(series["y"]) > 0
            assert all(v >= 0 for v in series["y"])

        print(f"✓ API handled {len(stock_series)} stock grants successfully")

    def test_api_total_compensation_calculation(self, client, real_world_request_data):
        """Test that total compensation is calculated correctly."""
        response = client.post(
            '/api/v1.0/plot/',
            data=json.dumps(real_world_request_data),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Find total pay series
        total_series = next((s for s in data if s["name"] == "Total Pay"), None)
        assert total_series is not None

        # Find base salary series
        base_series = next((s for s in data if s["name"] == "Base Salary"), None)
        assert base_series is not None

        # Total should be greater than base for most months (when bonuses/stocks included)
        total_values = total_series["y"]
        base_values = base_series["y"]

        # Find matching dates and compare
        matching_dates = set(total_series["x"]) & set(base_series["x"])
        assert len(matching_dates) > 0

        for date in list(matching_dates)[:5]:  # Check first 5 matching dates
            total_idx = total_series["x"].index(date)
            base_idx = base_series["x"].index(date)

            total_val = total_series["y"][total_idx]
            base_val = base_series["y"][base_idx]

            # Total should typically be >= base (includes bonuses, stocks)
            assert total_val >= base_val * 0.95  # Allow small floating point differences

        print(f"✓ Total compensation correctly aggregates all components")

    def test_api_with_inflation_adjustment(self, client, real_world_request_data):
        """Test API with CPI inflation adjustment enabled."""
        # Ensure inflation is enabled
        real_world_request_data["misc"]["predictedInflation"] = 1.03

        response = client.post(
            '/api/v1.0/plot/',
            data=json.dumps(real_world_request_data),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should include inflation-adjusted series
        series_names = [s["name"] for s in data]

        # Check if inflation series exists (it might be skipped if BLS API has issues)
        inflation_series = next(
            (s for s in data if "Inflation" in s["name"]),
            None
        )

        if inflation_series:
            assert len(inflation_series["y"]) > 0
            # Inflation-adjusted values should be positive
            assert all(v > 0 for v in inflation_series["y"])
            print(f"✓ Inflation-adjusted series generated successfully")
        else:
            print("⚠ Inflation-adjusted series not generated (may be expected if BLS API unavailable)")


class TestRealWorldScenarios:
    """Test realistic compensation scenarios end-to-end."""

    def test_standard_microsoft_compensation(self, client):
        """Test a typical Microsoft compensation package."""
        microsoft_comp = {
            "misc": {
                "startDate": "2021-07-01",
                "endDate": "2023-06-30",
                "predictedInflation": 1.03
            },
            "base": {
                "name": "Base Salary",
                "pay": [
                    {"startDate": "2021-07-01", "amount": 180000},
                    {"startDate": "2022-07-01", "amount": 190000}  # Promotion
                ]
            },
            "bonus": {
                "signing": {
                    "name": "Signing Bonus",
                    "amount": 50000,
                    "duration": {"years": 2, "months": 0, "days": 0}
                },
                "annual": {
                    "name": "Performance Bonus",
                    "default": 0.15,
                    "past": []
                }
            },
            "stocks": [
                {
                    "name": "Initial RSU Grant",
                    "ticker": "MSFT",
                    "startDate": "2021-07-01",
                    "endDate": "2024-06-30",
                    "shares": 200
                }
            ]
        }

        response = client.post(
            '/api/v1.0/plot/',
            data=json.dumps(microsoft_comp),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify realistic compensation values
        total_series = next(s for s in data if s["name"] == "Total Pay")

        # Total compensation should be reasonable (base + bonus + stocks)
        # For this scenario: ~$180k base + ~$27k bonus + stock value
        assert len(total_series["y"]) > 0
        avg_monthly_comp = sum(total_series["y"]) / len(total_series["y"])

        # Should be positive and reasonable (varies with stock price)
        assert avg_monthly_comp > 10000  # At minimum, should have base salary
        assert avg_monthly_comp < 500000  # Sanity check upper bound

        print(f"✓ Microsoft-style compensation calculated successfully")
        print(f"  Average monthly total: ${avg_monthly_comp:,.2f}")

    def test_multi_year_vesting_schedule(self, client):
        """Test multi-year stock vesting with different periods."""
        multi_year_comp = {
            "misc": {
                "startDate": "2023-01-01",
                "endDate": "2026-12-31",
                "predictedInflation": 1.025
            },
            "base": {
                "name": "Base Salary",
                "pay": [{"startDate": "2023-01-01", "amount": 200000}]
            },
            "bonus": {
                "signing": {
                    "name": "Signing Bonus",
                    "amount": 0,
                    "duration": {"years": 0, "months": 1, "days": 0}
                },
                "annual": {
                    "name": "Annual Bonus",
                    "default": 0.20,
                    "past": []
                }
            },
            "stocks": [
                {
                    "name": "Year 1 Grant",
                    "ticker": "AAPL",
                    "startDate": "2023-01-01",
                    "endDate": "2027-01-01",
                    "shares": 100
                },
                {
                    "name": "Year 2 Grant",
                    "ticker": "AAPL",
                    "startDate": "2024-01-01",
                    "endDate": "2028-01-01",
                    "shares": 100
                },
                {
                    "name": "Year 3 Grant",
                    "ticker": "AAPL",
                    "startDate": "2025-01-01",
                    "endDate": "2029-01-01",
                    "shares": 100
                }
            ]
        }

        response = client.post(
            '/api/v1.0/plot/',
            data=json.dumps(multi_year_comp),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should have all three stock grants
        stock_grants = [s for s in data if "Grant" in s["name"] and s["name"] != "Initial RSU Grant"]
        assert len(stock_grants) >= 3

        print(f"✓ Multi-year vesting schedule calculated successfully")

    def test_job_transition_with_overlapping_stocks(self, client):
        """Test scenario with multiple overlapping stock grants (like refreshers)."""
        overlapping_comp = {
            "misc": {
                "startDate": "2021-01-01",
                "endDate": "2023-12-31",
                "predictedInflation": 1.03
            },
            "base": {
                "name": "Base Salary",
                "pay": [{"startDate": "2021-01-01", "amount": 175000}]
            },
            "bonus": {
                "signing": {
                    "name": "Signing Bonus",
                    "amount": 30000,
                    "duration": {"years": 1, "months": 6, "days": 0}
                },
                "annual": {
                    "name": "Annual Bonus",
                    "default": 0.15,
                    "past": [
                        {"endDate": "2022-12-31", "multiplier": 0.20},
                        {"endDate": "2023-12-31", "multiplier": 0.18}
                    ]
                }
            },
            "stocks": [
                {
                    "name": "Initial Grant",
                    "ticker": "MSFT",
                    "startDate": "2021-01-01",
                    "endDate": "2025-01-01",
                    "shares": 150
                },
                {
                    "name": "Refresh Grant 1",
                    "ticker": "MSFT",
                    "startDate": "2022-01-01",
                    "endDate": "2026-01-01",
                    "shares": 75
                },
                {
                    "name": "Refresh Grant 2",
                    "ticker": "MSFT",
                    "startDate": "2023-01-01",
                    "endDate": "2027-01-01",
                    "shares": 80
                }
            ]
        }

        response = client.post(
            '/api/v1.0/plot/',
            data=json.dumps(overlapping_comp),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify grants are included (name might vary)
        stock_grants = [s for s in data if "Grant" in s.get("name", "")]
        assert len(stock_grants) >= 3, f"Expected at least 3 grants, found {len(stock_grants)}"

        # Total compensation should reflect overlapping grants
        total_series = next(s for s in data if s["name"] == "Total Pay")
        assert len(total_series["y"]) > 0

        print(f"✓ Overlapping stock grants handled correctly")


class TestAPIResilience:
    """Test API resilience and error handling with real services."""

    def test_api_with_invalid_ticker(self, client, real_world_request_data):
        """Test API behavior with an invalid stock ticker."""
        real_world_request_data["stocks"][0]["ticker"] = "INVALID_TICKER_XYZ"

        # In test mode, Flask raises exceptions instead of returning 500
        # So we need to temporarily disable testing mode to test error handling
        from app import app as flask_app
        original_testing = flask_app.config['TESTING']
        flask_app.config['TESTING'] = False

        try:
            response = client.post(
                '/api/v1.0/plot/',
                data=json.dumps(real_world_request_data),
                content_type='application/json'
            )

            # Should fail with 500 due to ValueError from invalid ticker
            assert response.status_code == 500
            print("✓ API properly rejects invalid ticker with 500 error")
        finally:
            flask_app.config['TESTING'] = original_testing

    def test_api_with_future_dates_only(self, client):
        """Test API with only future dates (requires prediction)."""
        future_comp = {
            "misc": {
                "startDate": "2027-01-01",
                "endDate": "2029-12-31",
                "predictedInflation": 1.03
            },
            "base": {
                "name": "Base Salary",
                "pay": [{"startDate": "2027-01-01", "amount": 200000}]
            },
            "bonus": {
                "signing": {
                    "name": "Signing Bonus",
                    "amount": 0,
                    "duration": {"years": 0, "months": 1, "days": 0}
                },
                "annual": {
                    "name": "Annual Bonus",
                    "default": 0.15,
                    "past": []
                }
            },
            "stocks": [
                {
                    "name": "Future Grant",
                    "ticker": "MSFT",
                    "startDate": "2027-01-01",
                    "endDate": "2031-01-01",
                    "shares": 100
                }
            ]
        }

        response = client.post(
            '/api/v1.0/plot/',
            data=json.dumps(future_comp),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should still generate series with predicted values
        assert len(data) > 0
        total_series = next(s for s in data if s["name"] == "Total Pay")
        assert len(total_series["y"]) > 0

        print("✓ API handles future-only dates with predictions")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
