# load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Import Flask and render_template
from flask import Flask, request
from flask_cors import cross_origin
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import dateutil.parser as dparser
import os
import json
import pandas as pd
import math
from cpi import inflater
from stocks import price_tracker

STATIC_ROOT = os.getenv('STATIC_ROOT')
DISABLE_INFLATION = os.getenv('DISABLE_INFLATION')
if DISABLE_INFLATION == None:
    DISABLE_INFLATION = False
else:
    DISABLE_INFLATION = DISABLE_INFLATION.lower() == "true"

cpi = inflater()

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

    series = []

    series.append(getBaseSeries(data))
    series.append(getAnnualBonusSeries(data))
    series.append(getSigningBonusSeries(data))

    for stock in data["stocks"]:
        series.append(getStockSeries(stock, data))

    totalPaySeries = getTotalPaySeries(data, serieses=series)
    series.append(totalPaySeries)

    try:
        if not(DISABLE_INFLATION):
            series.append(getInflationAdjustedStartingPaySeries(data, totalPaySeries))
    except Exception as e:
        print("Skipping inflation line due to exception: \n%s" % str(e))
    
    # get preloaded response json
    return json.dumps(series, default=str)

def getTotalPaySeries(data: dict, serieses: list) -> dict:
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

def getInflationAdjustedStartingPaySeries(data: dict, totalPaySeries: dict) -> dict:
    startDate = dparser.parse(data["misc"]["startDate"])
    endDate = dparser.parse(data["misc"]["endDate"])

    predictedInflation = data["misc"]["predictedInflation"]

    x = [x for x in pd.date_range(
        start=startDate,
        end=endDate,
        freq="MS")]
    
    startingPay = totalPaySeries["y"][0]
    startDate = x[0].date()

    y = [cpi.inflate(startingPay, startDate, date.date(), predictedInflation=predictedInflation) for date in x]

    series = dict()
    series["name"] = "Inflation Adjusted Starting Pay"
    series["x"] = x
    series["y"] = y
    series["visible"] = "legendonly"
    series["type"] = "scatter"
    series["line"] = { "shape": "hv" }

    return series


def getStockSeries(stock: dict, data: dict) -> dict:
    predictedInflation = data["misc"]["predictedInflation"]
    ticker = stock["ticker"]

    # object to track stock price live
    tracker = price_tracker(predictedInflation, ticker)

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


def getSigningBonusSeries(data: dict) -> dict:
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
def get_base_pay(date: datetime, sortedPay: list) -> float:

    for tup in sortedPay:
        startDate = dparser.parse(tup["startDate"])
        amount = tup["amount"]

        if date > startDate:
            return amount
        
    return 0

def getBaseSeries(data: dict) -> dict:
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
def get_annual_bonus_pay(date: datetime, sortedPay: list, sortedBonuses: list, default: float) -> float:

    base_pay = get_base_pay(date=date, sortedPay=sortedPay)

    multiplier: float = default
    for tup in sortedBonuses:
        endDate = dparser.parse(tup["endDate"])

        if date <= endDate and date > endDate - relativedelta(years=1):
            multiplier: float = tup["multiplier"]
            break
        
    return base_pay * multiplier

def getAnnualBonusSeries(data: dict) -> dict:
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
