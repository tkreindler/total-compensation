import requests
from requests import Response
from datetime import date
import math
import os

_api_url = "https://api.bls.gov/publicAPI/v1/timeseries/data/"

# optional API key to use with the BLS for higher limits
BLS_API_KEY = os.getenv('BLS_API_KEY')

class inflater:
    """
    A class for easily price adjusting values according the the BLS CPI
    values for different years.

    Was created as a far more lightweight alternative to https://pypi.org/project/cpi/.

    Sacrifices a little bit of speed upon initial execution for much lower memory usage
    and a far faster initialization time.
    """
    def __init__(self, seriesId: str = 'CUUR0000SA0L1E'):
        """
        Create an instance of inflater

        Parameters:
        seriesId (str):
        The identifier of the BLS CPI series to use
        CUUR0000SA0L1E is the default CPI-U but there are literally hundreds to choose from
        See https://www.bls.gov/help/hlpforma.htm
        """

        self.seriesId: str = seriesId

        # a dictionary of year -> array of cpi values by month
        self.cpi_data: dict[int, list[float | None]] = {}

        # get data on the latest year/month so we can use it for calculating predictedInflation
        request_data = { 'seriesid': [ self.seriesId ] }
        if BLS_API_KEY != None:
            request_data["registrationKey"] = BLS_API_KEY

        response = requests.post(_api_url, json = request_data)

        series = self._process_bls_response(response)

        # Find the first entry with a valid value (not '-')
        latest_entry = next((x for x in series if x["value"] != '-'), series[0])
        
        self.latest_year = int(latest_entry["year"])
        self.latest_month = int(latest_entry["period"][1:])
        self.latest_value = float(latest_entry["value"])
        
        self._consume_series(series)


    def get_cpi_value(self, date: date, predictedInflation: float | None = None) -> float:
        """
        Get the CSI value from the BLS api for a specific date.
        Note that the accuracy is only monthly so the days on
        the date value are ignored.

        Parameters:
        date (date):
        The date to get the CPI value of (monthly accuracy).

        predictedInflation (float | None):
        The predicted inflation to use for future calculations.
        If "None" will throw on future calculations.
        If 1.03 will assume 3% yearly inflation for all future dates without CPI data.

        Returns:
        The value from the API in float form.
        """

        if date.year > self.latest_year or (date.year == self.latest_year and date.month > self.latest_month):
            return self._get_predicted_cpi_value(date, predictedInflation)
        
        if date.year not in self.cpi_data:
            self._load_data_from_api(date.year)

        val: float | None = self.cpi_data[date.year][date.month - 1]
        if val == None:
            raise Exception("Value was unexpected null")
        
        return val
            
            
    def _load_data_from_api(self, year: int):
        # get the ten year span (inclusive) surrounding this year to minimize API requests
        minYear = year - 4
        maxYear = year + 5

        request_data = {
            'seriesid': [
                self.seriesId
            ],
            'startyear': minYear,
            'endyear': maxYear
        }
        if BLS_API_KEY != None:
            request_data["registrationKey"] = BLS_API_KEY

        response = requests.post(_api_url, json = request_data)

        series = self._process_bls_response(response)
        self._consume_series(series)

        if year not in self.cpi_data:
            raise Exception("CPI data for year %d still not found after requesting from the BLS API." % year)


    def _get_predicted_cpi_value(self, date: date, predictedInflation: float | None) -> float:
        """
        If predictedInflation == None just throw - predicted inflation isn't enabled.

        If it is enabled simply plug the values into the continuously compounding interest
        forumula and plug out an answer using the predicted inflation rate from the last month
        that we know about.

        Returns the cpi value in float form.
        """

        if predictedInflation == None:
            raise Exception("Predicting future inflation is not enabled. Can't process date %s. \
Set a predictedInflation value in the constructor if you want this functionality." % str(date))
        if predictedInflation < 0.5:
            raise Exception("""
Predicted inflation value cannot be less than 0.5.
Baseline is at 1, anything less than 1 would be deflation.
For example, if you want 3 percent inflation use 1.03.

Did you mean to add 1 from the value you used?
""")
        
        monthsDifference = (date.year - self.latest_year) * 12 + date.month - self.latest_month
        yearsDifference = monthsDifference / 12
        r = predictedInflation - 1

        multiplier = math.e ** (r * yearsDifference)
        val = self.latest_value * multiplier
        return val


    def inflate(self, value: float, startDate: date, endDate: date, predictedInflation: float | None = None) -> float:
        """
        Inflate a value (price) from the startDate and get its equivelant price
        at the endDate using CPI numbers from the BLS API.

        Parameters:
        value (float):
        The value (price) at the startDate to adjust.

        startDate (date):
        The start date the value parameter is assumed to be from.

        endDate (date):
        The end date to adjust the price of value to.

        predictedInflation (float | None):
        The predicted inflation to use for future calculations.
        If "None" will throw on future calculations.
        If 1.03 will assume 3% yearly inflation for all future dates without CPI data.
        
        Returns:
        The corresponding inflated value at the endDate.

        """
        
        startCpiVal = self.get_cpi_value(startDate, predictedInflation=predictedInflation)
        endCpiVal = self.get_cpi_value(endDate, predictedInflation=predictedInflation)

        return value * endCpiVal / startCpiVal


    def _process_bls_response(self, response: Response) -> list[dict[str, str]]:
        """
        Takes a response object from the BLS API and does some standard assertions
        and data processing.

        Returns the json decoded data from response.Results.series[0].data. Assumes a single
        series will be returned which should always be the case for this application.
        """

        if (response.status_code // 100 != 2):
            raise Exception("BLS API returned unexpected status code %d with response %s" % (response.status_code, response.text))

        json: dict = response.json()

        if (json["status"] != "REQUEST_SUCCEEDED"):
            raise Exception("BLS API returned unexpected response")
        
        numSeries = len(json["Results"]["series"])
        if (numSeries != 1):
            raise Exception("BLS API returned unexpected number of series %d" % numSeries)

        series = json["Results"]["series"][0]["data"]

        return series


    def _consume_series(self, series: list[dict[str, str]]) -> None:
        """
        Consumes a certain year from a series. The series should be the value
        processed by _process_bls_response after sending a request to the
        BLS API and getting a response back.

        By "consuming" it we mean the data is formatted and added to self.cpi_data
        in the appropriate manner.
        """
        years = {int(x["year"]) for x in series}

        for year in years:
            series_for_year = [x for x in series if int(x["year"]) == year]

            latest_year_data = [None for _ in range(12)]

            for x in series_for_year:
                month = int(x["period"][1:])
                # Skip entries with missing data (represented as '-')
                if x["value"] == '-':
                    continue
                value = float(x["value"])

                latest_year_data[month - 1] = value
            
            self.cpi_data[year] = latest_year_data
