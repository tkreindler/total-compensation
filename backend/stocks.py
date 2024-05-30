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
        self.currentPrice: float = self.ticker.info["currentPrice"]
        
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