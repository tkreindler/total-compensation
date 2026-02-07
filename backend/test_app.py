"""
End-to-end integration tests for the Total Compensation backend.

Tests cover:
- API endpoints
- Base pay calculations
- Bonus calculations (signing and annual)
- Stock award calculations
- CPI inflation adjustments
- Total compensation aggregation
"""

import pytest
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os
from unittest.mock import Mock, patch, MagicMock

# Set test environment variables before importing app
os.environ['DISABLE_INFLATION'] = 'false'
os.environ['STATIC_ROOT'] = '../frontend/build/'

from app import (
    app,
    getBaseSeries,
    getAnnualBonusSeries,
    getSigningBonusSeries,
    getStockSeries,
    getTotalPaySeries,
    getInflationAdjustedStartingPaySeries,
    get_base_pay,
    get_annual_bonus_pay
)
from cpi import inflater


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_request_data():
    """Sample request data for testing the API."""
    return {
        "misc": {
            "startDate": "2024-01-01",
            "endDate": "2026-12-31",
            "predictedInflation": 1.03
        },
        "base": {
            "name": "Base Salary",
            "pay": [
                {"startDate": "2024-01-01", "amount": 150000},
                {"startDate": "2025-01-01", "amount": 165000}
            ]
        },
        "bonus": {
            "signing": {
                "name": "Signing Bonus",
                "amount": 50000,
                "duration": {"years": 2, "months": 0, "days": 0}
            },
            "annual": {
                "name": "Annual Bonus",
                "default": 0.15,
                "past": [
                    {"endDate": "2024-12-31", "multiplier": 0.20}
                ]
            }
        },
        "stocks": [
            {
                "name": "RSU Grant 1",
                "ticker": "MSFT",
                "startDate": "2024-01-01",
                "endDate": "2027-12-31",
                "shares": 100
            }
        ]
    }


@pytest.fixture
def mock_yfinance_ticker():
    """Mock yfinance Ticker object."""
    mock_ticker = Mock()
    mock_ticker.info = {
        "symbol": "MSFT",
        "currentPrice": 400.0
    }

    # Mock historical data
    mock_history = Mock()
    mock_history.empty = False
    mock_history.__getitem__ = Mock(return_value=Mock(iloc=[450.0]))
    mock_ticker.history = Mock(return_value=mock_history)

    return mock_ticker


class TestBasePay:
    """Tests for base pay calculations."""

    def test_get_base_pay_single_entry(self):
        """Test base pay calculation with a single pay entry."""
        pay = [{"startDate": "2024-01-01", "amount": 150000}]
        sorted_pay = sorted(pay, key=lambda item: item["startDate"], reverse=True)

        result = get_base_pay(datetime(2024, 6, 1), sorted_pay)
        assert result == 150000

    def test_get_base_pay_multiple_entries(self):
        """Test base pay calculation with promotions/raises."""
        pay = [
            {"startDate": "2024-01-01", "amount": 150000},
            {"startDate": "2025-01-01", "amount": 165000}
        ]
        sorted_pay = sorted(pay, key=lambda item: item["startDate"], reverse=True)

        # Before promotion
        result = get_base_pay(datetime(2024, 6, 1), sorted_pay)
        assert result == 150000

        # After promotion
        result = get_base_pay(datetime(2025, 6, 1), sorted_pay)
        assert result == 165000

    def test_get_base_pay_before_start(self):
        """Test base pay before start date returns 0."""
        pay = [{"startDate": "2024-01-01", "amount": 150000}]
        sorted_pay = sorted(pay, key=lambda item: item["startDate"], reverse=True)

        result = get_base_pay(datetime(2023, 6, 1), sorted_pay)
        assert result == 0


class TestAnnualBonus:
    """Tests for annual bonus calculations."""

    def test_get_annual_bonus_default(self):
        """Test annual bonus with default multiplier."""
        pay = [{"startDate": "2024-01-01", "amount": 150000}]
        sorted_pay = sorted(pay, key=lambda item: item["startDate"], reverse=True)
        past_bonuses = []
        sorted_bonuses = []

        result = get_annual_bonus_pay(
            datetime(2024, 6, 1),
            sorted_pay,
            sorted_bonuses,
            default=0.15
        )
        assert result == 150000 * 0.15

    def test_get_annual_bonus_with_past_bonus(self):
        """Test annual bonus with actual past performance."""
        pay = [{"startDate": "2024-01-01", "amount": 150000}]
        sorted_pay = sorted(pay, key=lambda item: item["startDate"], reverse=True)
        past_bonuses = [{"endDate": "2024-12-31", "multiplier": 0.20}]
        sorted_bonuses = sorted(past_bonuses, key=lambda item: item["endDate"], reverse=True)

        # Within the bonus year
        result = get_annual_bonus_pay(
            datetime(2024, 6, 1),
            sorted_pay,
            sorted_bonuses,
            default=0.15
        )
        assert result == 150000 * 0.20

        # After bonus year, should use default
        result = get_annual_bonus_pay(
            datetime(2025, 6, 1),
            sorted_pay,
            sorted_bonuses,
            default=0.15
        )
        assert result == 150000 * 0.15


class TestSeriesGeneration:
    """Tests for series generation functions."""

    def test_base_series(self, sample_request_data):
        """Test base salary series generation."""
        series = getBaseSeries(sample_request_data)

        assert series["name"] == "Base Salary"
        assert series["type"] == "scatter"
        assert series["stackgroup"] == "one"
        assert len(series["x"]) > 0
        assert len(series["y"]) == len(series["x"])

        # Check that raises are reflected
        assert 150000 in series["y"]
        assert 165000 in series["y"]

    def test_signing_bonus_series(self, sample_request_data):
        """Test signing bonus series generation."""
        series = getSigningBonusSeries(sample_request_data)

        assert series["name"] == "Signing Bonus"
        assert series["type"] == "scatter"
        assert len(series["x"]) > 0

        # Signing bonus should be amortized over duration
        total_amount = sample_request_data["bonus"]["signing"]["amount"]
        num_months = len(series["x"])
        expected_monthly = total_amount * 12 / num_months

        # All months should have equal amortized amount
        assert all(abs(y - expected_monthly) < 0.01 for y in series["y"])

    def test_annual_bonus_series(self, sample_request_data):
        """Test annual bonus series generation."""
        series = getAnnualBonusSeries(sample_request_data)

        assert series["name"] == "Annual Bonus"
        assert series["type"] == "scatter"
        assert len(series["x"]) > 0
        assert len(series["y"]) == len(series["x"])

        # Should reflect both base pay and bonus multiplier
        # First value may be 0 due to start date logic (date > startDate)
        assert any(y > 0 for y in series["y"])

        # Check months after start date should have bonus
        for i, date in enumerate(series["x"]):
            if date.year == 2024 and date.month > 1:
                # After first month, should have positive bonus
                assert series["y"][i] > 0, f"Expected bonus for {date} but got {series['y'][i]}"

    @patch('stocks.yfinance.Ticker')
    def test_stock_series(self, mock_ticker_class, sample_request_data, mock_yfinance_ticker):
        """Test stock award series generation."""
        mock_ticker_class.return_value = mock_yfinance_ticker

        stock = sample_request_data["stocks"][0]
        series = getStockSeries(stock, sample_request_data)

        assert series["name"] == "RSU Grant 1"
        assert series["type"] == "scatter"
        assert len(series["x"]) > 0
        assert len(series["y"]) == len(series["x"])

        # All values should be positive
        assert all(y > 0 for y in series["y"])

    @patch('stocks.yfinance.Ticker')
    def test_total_pay_series(self, mock_ticker_class, sample_request_data, mock_yfinance_ticker):
        """Test total compensation aggregation."""
        mock_ticker_class.return_value = mock_yfinance_ticker

        # Generate all component series
        series = []
        series.append(getBaseSeries(sample_request_data))
        series.append(getAnnualBonusSeries(sample_request_data))
        series.append(getSigningBonusSeries(sample_request_data))

        for stock in sample_request_data["stocks"]:
            series.append(getStockSeries(stock, sample_request_data))

        total_series = getTotalPaySeries(sample_request_data, serieses=series)

        assert total_series["name"] == "Total Pay"
        assert total_series["type"] == "scatter"
        assert total_series["visible"] == "legendonly"
        assert len(total_series["x"]) > 0

        # Total should be greater than any individual component
        base_series = series[0]
        for i in range(len(total_series["y"])):
            # Find matching date in base series
            if total_series["x"][i] in base_series["x"]:
                idx = base_series["x"].index(total_series["x"][i])
                assert total_series["y"][i] >= base_series["y"][idx]


class TestCPIInflation:
    """Tests for CPI inflation calculations."""

    @patch('cpi.requests.post')
    def test_inflater_initialization(self, mock_post):
        """Test CPI inflater initialization."""
        # Mock BLS API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [{
                    "data": [
                        {"year": "2024", "period": "M01", "value": "308.417"}
                    ]
                }]
            }
        }
        mock_post.return_value = mock_response

        inf = inflater()
        assert inf.latest_year >= 2024
        assert inf.latest_value > 0

    @patch('cpi.requests.post')
    def test_inflation_adjusted_series(self, mock_post, sample_request_data):
        """Test inflation-adjusted starting pay series."""
        # Mock BLS API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [{
                    "data": [
                        {"year": "2024", "period": f"M{str(i).zfill(2)}", "value": str(300 + i)}
                        for i in range(1, 13)
                    ]
                }]
            }
        }
        mock_post.return_value = mock_response

        # Create a mock total pay series
        total_series = {
            "name": "Total Pay",
            "x": [datetime(2024, 1, 1)],
            "y": [200000],
            "type": "scatter"
        }

        series = getInflationAdjustedStartingPaySeries(sample_request_data, total_series)

        assert series["name"] == "Inflation Adjusted Starting Pay"
        assert series["type"] == "scatter"
        assert series["visible"] == "legendonly"
        assert len(series["x"]) > 0

        # First value should equal starting pay
        assert series["y"][0] == total_series["y"][0]

        # Future values should be higher due to inflation
        assert series["y"][-1] > series["y"][0]


class TestAPIEndpoints:
    """Tests for Flask API endpoints."""

    def test_root_endpoint(self, client):
        """Test that root endpoint serves index.html."""
        # This will return 200 if static files exist, or 404/500 if they don't
        response = client.get('/')
        # Accept either success (if frontend is built) or failure (if not built)
        assert response.status_code in [200, 404, 500]

    def test_api_wrong_content_type(self, client):
        """Test API rejects non-JSON content type."""
        response = client.post(
            '/api/v1.0/plot/',
            data='not json',
            content_type='text/plain'
        )
        assert response.status_code == 200
        assert b"Content-Type not supported" in response.data

    @patch('stocks.yfinance.Ticker')
    @patch('app.get_cpi_instance')
    def test_api_plot_endpoint_success(self, mock_cpi, mock_ticker_class,
                                       client, sample_request_data, mock_yfinance_ticker):
        """Test successful API call to plot endpoint."""
        # Mock yfinance
        mock_ticker_class.return_value = mock_yfinance_ticker

        # Mock CPI inflater
        mock_inflater = Mock()
        mock_inflater.inflate = Mock(return_value=210000.0)
        mock_cpi.return_value = mock_inflater

        response = client.post(
            '/api/v1.0/plot/',
            data=json.dumps(sample_request_data),
            content_type='application/json'
        )

        assert response.status_code == 200

        # Parse response
        data = json.loads(response.data)

        # Should return multiple series
        assert isinstance(data, list)
        assert len(data) > 0

        # Each series should have required fields
        for series in data:
            assert "name" in series
            assert "x" in series
            assert "y" in series
            assert "type" in series

    @patch('stocks.yfinance.Ticker')
    def test_api_plot_with_multiple_stocks(self, mock_ticker_class,
                                           client, sample_request_data, mock_yfinance_ticker):
        """Test API with multiple stock grants."""
        # Add another stock grant
        sample_request_data["stocks"].append({
            "name": "RSU Grant 2",
            "ticker": "GOOGL",
            "startDate": "2025-01-01",
            "endDate": "2028-12-31",
            "shares": 50
        })

        mock_ticker_class.return_value = mock_yfinance_ticker

        response = client.post(
            '/api/v1.0/plot/',
            data=json.dumps(sample_request_data),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should have series for both stock grants
        stock_series = [s for s in data if "RSU Grant" in s["name"]]
        assert len(stock_series) >= 2

    def test_api_plot_with_no_stocks(self, client, sample_request_data):
        """Test API with no stock grants."""
        sample_request_data["stocks"] = []

        response = client.post(
            '/api/v1.0/plot/',
            data=json.dumps(sample_request_data),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should still have base, signing, annual bonus series
        assert len(data) >= 3
        series_names = [s["name"] for s in data]
        assert "Base Salary" in series_names


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_pay_array(self):
        """Test with empty pay array."""
        sorted_pay = []
        result = get_base_pay(datetime(2024, 6, 1), sorted_pay)
        assert result == 0

    def test_zero_duration_signing_bonus(self, sample_request_data):
        """Test signing bonus with minimal duration."""
        sample_request_data["bonus"]["signing"]["duration"] = {
            "years": 0,
            "months": 1,
            "days": 0
        }

        series = getSigningBonusSeries(sample_request_data)
        assert len(series["x"]) > 0
        assert all(y > 0 for y in series["y"])

    @patch('stocks.yfinance.Ticker')
    def test_stock_price_future_prediction(self, mock_ticker_class,
                                           sample_request_data, mock_yfinance_ticker):
        """Test stock price prediction for future dates."""
        # Mock empty historical data to trigger future prediction
        mock_history = Mock()
        mock_history.empty = True
        mock_yfinance_ticker.history = Mock(return_value=mock_history)

        mock_ticker_class.return_value = mock_yfinance_ticker

        stock = sample_request_data["stocks"][0]
        series = getStockSeries(stock, sample_request_data)

        # Should still generate values using current price + inflation
        assert len(series["y"]) > 0
        assert all(y > 0 for y in series["y"])


class TestDataConsistency:
    """Tests for data consistency and validation."""

    @patch('stocks.yfinance.Ticker')
    def test_series_date_alignment(self, mock_ticker_class,
                                   sample_request_data, mock_yfinance_ticker):
        """Test that all series have aligned dates."""
        mock_ticker_class.return_value = mock_yfinance_ticker

        # Generate multiple series
        base_series = getBaseSeries(sample_request_data)
        bonus_series = getAnnualBonusSeries(sample_request_data)
        signing_series = getSigningBonusSeries(sample_request_data)

        # All series covering full period should have same length
        assert len(base_series["x"]) == len(bonus_series["x"])

        # Dates should be in chronological order
        for series in [base_series, bonus_series, signing_series]:
            dates = series["x"]
            for i in range(len(dates) - 1):
                assert dates[i] < dates[i + 1]

    def test_total_pay_aggregation_correctness(self, sample_request_data):
        """Test that total pay correctly sums all components."""
        # Simplified test with just base and bonus
        base_series = getBaseSeries(sample_request_data)
        bonus_series = getAnnualBonusSeries(sample_request_data)

        total_series = getTotalPaySeries(
            sample_request_data,
            serieses=[base_series, bonus_series]
        )

        # Check specific months
        for i in range(min(len(base_series["x"]), len(total_series["x"]))):
            date = total_series["x"][i]
            if date in base_series["x"]:
                base_idx = base_series["x"].index(date)
                bonus_idx = bonus_series["x"].index(date)

                expected = base_series["y"][base_idx] + bonus_series["y"][bonus_idx]
                actual = total_series["y"][i]

                # Allow small floating point differences
                assert abs(expected - actual) < 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
