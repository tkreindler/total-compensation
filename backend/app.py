# Import Flask and render_template
from flask import Flask, request
from flask_cors import cross_origin
import yfinance
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import dateutil.parser as dparser
import os
import json
import pandas as pd
import math
from dotenv import load_dotenv

load_dotenv()

STATIC_ROOT = os.getenv('STATIC_ROOT')

print("Loading yfinance ticker, this might take a while...")
ticker = yfinance.Ticker("MSFT")
print("Finished loading yfinance ticker")

currentPrice = ticker.info["currentPrice"]

# refresh cpi data
print("Updating cpi data, this might take a while...")
import cpi

class price_tracker:
    def __init__(self, predictedInflation):
        # Get the ticker object
        self.predictedInflation = predictedInflation
        
        self.cutOffDate = None

    def get_price(self, date):
        if self.cutOffDate and date > self.cutOffDate:
            yearsSince = (date - self.cutOffDate).days / 365

            return currentPrice * (self.predictedInflation ** yearsSince)

        # Get the historical data for the date
        data = ticker.history(start=date, end=date + relativedelta(days=7))

        if not(data.empty):
            price = data["Close"].iloc[0]

            return price
        
        # make it more efficient by storing this as the last allowed date in perpetuity
        self.cutOffDate = date
        return currentPrice

# Create a Flask app instance, serving static assets
app = Flask(__name__, static_folder=STATIC_ROOT, static_url_path="/static/")

# serve index.html as the root path
@app.route('/')
def root():
    return app.send_static_file('index.html')

# Define the API endpoint that returns a JSON response
@app.route("/api/v1.0/plot/", methods=["POST"])
@cross_origin()
def api():
    content_type = request.headers.get("Content-Type")
    if content_type != "application/json":
        return "Content-Type not supported!"
    
    data = request.get_json()

    predictedInflation = data["misc"]["predictedInflation"]

    # object to track stock price live
    tracker = price_tracker(predictedInflation=predictedInflation)

    series = []

    series.append(getBaseSeries(data))
    series.append(getAnnualBonusSeries(data))
    series.append(getSigningBonusSeries(data))

    for stock in data["stocks"]:
        series.append(getStockSeries(stock, tracker))

    totalPaySeries = getTotalPaySeries(data, serieses=series)
    series.append(totalPaySeries)

    series.append(getInflationAdjustedStartingPaySeries(data, totalPaySeries))
    
    # get preloaded response json
    return json.dumps(series, default=str)

def getTotalPaySeries(data: {}, serieses: []):
    startDate = dparser.parse(data["misc"]["startDate"])
    endDate = dparser.parse(data["misc"]["endDate"])

    x = [x for x in pd.date_range(
        start=startDate,
        end=endDate,
        freq="MS")]
    y = []
    for date in x:
        total = 0
        for other in serieses:
            try:
                i = other["x"].index(date)
                total += other["y"][i]
            except:
                pass
        y.append(total)

    series = dict()
    series["name"] = "Total Pay"
    series["x"] = x
    series["y"] = y
    series["visible"] = "legendonly"
    series["type"] = "scatter"
    series["line"] = { "shape": "hv" }

    return series

def getInflationAdjustedStartingPaySeries(data: {}, totalPaySeries: {}):
    startDate = dparser.parse(data["misc"]["startDate"])
    endDate = dparser.parse(data["misc"]["endDate"])

    predictedInflation = data["misc"]["predictedInflation"]

    x = [x for x in pd.date_range(
        start=startDate,
        end=endDate,
        freq="MS")]
    
    startingPay = totalPaySeries["y"][0]
    startDate = x[0].date()

    lastDate = None
    lastValue = None

    y = []
    for date in x:
        try:
            pay = cpi.inflate(startingPay, startDate, date.date())

            lastDate = date
            lastValue = pay

            y.append(pay)
        except:
            # use the predicted inflation value to extrapolate future dates it doesn't have yet
            # assume 365.25 days in a year for simplicity
            yearsPassed = (date - lastDate) / timedelta(days=365.25)

            # assume continuously compounding interest for simplicity
            pay = lastValue * (math.e ** (yearsPassed * (predictedInflation - 1)))

            y.append(pay)

    series = dict()
    series["name"] = "Inflation Adjusted Starting Pay"
    series["x"] = x
    series["y"] = y
    series["visible"] = "legendonly"
    series["type"] = "scatter"
    series["line"] = { "shape": "hv" }

    return series


def getStockSeries(stock: {}, tracker: price_tracker):
    startDate = dparser.parse(stock["startDate"])
    endDate = dparser.parse(stock["endDate"])

    numShares = stock["shares"]

    x = [x for x in pd.date_range(start=startDate, end=endDate, freq="MS")]
    y = [numShares * tracker.get_price(date) * 12 / len(x) for date in x]

    series = dict()
    series["name"] = stock["name"]
    series["x"] = x
    series["y"] = y
    series["stackgroup"] = "one"
    series["type"] = "scatter"
    series["line"] = { "shape": "hv" }

    return series


def getSigningBonusSeries(data: {}):
    startDate = dparser.parse(data["misc"]["startDate"])

    duration = relativedelta(
        years=data["bonus"]["signing"]["duration"].get("years", 0),
        months=data["bonus"]["signing"]["duration"].get("months", 0),
        days=data["bonus"]["signing"]["duration"].get("days", 0),
    )

    endDate = startDate + duration

    amount = data["bonus"]["signing"]["amount"]

    x = [x for x in pd.date_range(
        start=startDate,
        end=endDate,
        freq="MS")]

    y = [ amount * 12 / len(x) for month in x]

    series = dict()
    series["name"] = data["bonus"]["signing"]["name"]
    series["x"] = x
    series["y"] = y
    series["stackgroup"] = "one"
    series["type"] = "scatter"
    series["line"] = { "shape": "hv" }

    return series

# Base pay switch statment, put promotions here as they come
def get_base_pay(date: datetime, sortedPay: list):

    for tup in sortedPay:
        startDate = dparser.parse(tup["startDate"])
        amount = tup["amount"]

        if date > startDate:
            return amount
        
    return 0

def getBaseSeries(data: {}):
    startDate = dparser.parse(data["misc"]["startDate"])
    endDate = dparser.parse(data["misc"]["endDate"])

    x = [x for x in pd.date_range(
        start=startDate,
        end=endDate,
        freq="MS")]

    pay: list = data["base"]["pay"]
    sortedPay = sorted(pay, key=lambda item: item["startDate"], reverse=True)

    y = [get_base_pay(month, sortedPay=sortedPay) for month in x]

    series = dict()
    series["name"] = data["base"]["name"]
    series["x"] = x
    series["y"] = y
    series["stackgroup"] = "one"
    series["type"] = "scatter"
    series["line"] = { "shape": "hv" }

    return series

# Base pay switch statment, put promotions here as they come
def get_annual_bonus_pay(date: datetime, sortedPay: list, sortedBonuses: list, default: float):

    base_pay = get_base_pay(date=date, sortedPay=sortedPay)

    multiplier: float = default
    for tup in sortedBonuses:
        endDate = dparser.parse(tup["endDate"])

        if date <= endDate and date > endDate - relativedelta(years=1):
            multiplier: float = tup["multiplier"]
            break
        
    return base_pay * multiplier

def getAnnualBonusSeries(data: {}):
    startDate = dparser.parse(data["misc"]["startDate"])
    endDate = dparser.parse(data["misc"]["endDate"])
    default = data["bonus"]["annual"]["default"]

    x = [x for x in pd.date_range(
        start=startDate,
        end=endDate,
        freq="MS")]

    pay: list = data["base"]["pay"]
    sortedPay = sorted(pay, key=lambda item: item["startDate"], reverse=True)

    pastBonuses: list = data["bonus"]["annual"]["past"]
    sortedBonuses = sorted(pastBonuses, key=lambda item: item["endDate"], reverse=True)

    y = [get_annual_bonus_pay(month, sortedPay=sortedPay, sortedBonuses=sortedBonuses, default=default) for month in x]

    series = dict()
    series["name"] = data["bonus"]["annual"]["name"]
    series["x"] = x
    series["y"] = y
    series["stackgroup"] = "one"
    series["type"] = "scatter"
    series["line"] = { "shape": "hv" }

    return series


# Run the app in debug mode
if __name__ == "__main__":
    app.run(debug=True)
