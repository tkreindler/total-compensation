import yfinance
from yfinance import Ticker
from datetime import date
import math
from dateutil.relativedelta import relativedelta

ticker_cache: dict[str, Ticker] = {}

class price_tracker:
    def __init__(self, predictedInflation: float, ticker: str):
        if ticker not in ticker_cache:
            print("Loading yfinance ticker for %s, this might take a while..." % ticker)
            ticker_cache[ticker] = yfinance.Ticker(ticker)
            print("Finished loading yfinance ticker for %s" % ticker)
        self.ticker = ticker_cache[ticker]

        # Get the ticker object
        self.predictedInflation = predictedInflation

        # Try to get current price from various possible fields
        info = self.ticker.info

        # Validate we got actual ticker data (invalid tickers lack 'symbol' field)
        if "symbol" not in info or info.get("symbol") is None:
            raise ValueError(
                f"Invalid or delisted ticker symbol: '{ticker}'. "
                f"Please verify the ticker symbol is correct and actively traded."
            )

        self.currentPrice: float | None = (
            info.get("currentPrice") or
            info.get("regularMarketPrice") or
            info.get("previousClose")
        )

        if self.currentPrice is None or self.currentPrice <= 0:
            raise ValueError(
                f"Could not fetch current price for ticker '{ticker}'. "
                f"The ticker may be delisted, have no trading activity, or be invalid. "
                f"Available price data: currentPrice={info.get('currentPrice')}, "
                f"regularMarketPrice={info.get('regularMarketPrice')}, "
                f"previousClose={info.get('previousClose')}"
            )

        self.cutOffDate: date | None = None

    def get_price(self, date: date) -> float:
        if self.cutOffDate and date > self.cutOffDate:
            yearsDifference: float = (date - self.cutOffDate).days / 365.25

            # continously compound interest
            r: float = self.predictedInflation - 1

            multiplier: float = math.e ** (r * yearsDifference)
            val: float = self.currentPrice * multiplier

            return val

        # Get the historical data for the date
        data = self.ticker.history(start=date, end=date + relativedelta(days=7))

        if not(data.empty):
            price: float = data["Close"].iloc[0]

            return price
        
        # make it more efficient by storing this as the last allowed date in perpetuity
        self.cutOffDate = date
        return self.currentPrice