import yfinance
import math
from dateutil.relativedelta import relativedelta

print("Loading yfinance ticker, this might take a while...")
_ticker = yfinance.Ticker("MSFT")
print("Finished loading yfinance ticker")

class price_tracker:
    def __init__(self, predictedInflation):
        # Get the ticker object
        self.predictedInflation = predictedInflation
        self.currentPrice = _ticker.info["currentPrice"]
        
        self.cutOffDate = None

    def get_price(self, date):
        if self.cutOffDate and date > self.cutOffDate:
            yearsDifference = (date - self.cutOffDate).days / 365.25

            # continously compound interest
            r = self.predictedInflation - 1

            multiplier = math.e ** (r * yearsDifference)
            val = self.currentPrice * multiplier

            return val

        # Get the historical data for the date
        data = _ticker.history(start=date, end=date + relativedelta(days=7))

        if not(data.empty):
            price = data["Close"].iloc[0]

            return price
        
        # make it more efficient by storing this as the last allowed date in perpetuity
        self.cutOffDate = date
        return self.currentPrice