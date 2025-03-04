import pandas as pd
import backtrader as bt
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
from tvDatafeed import TvDatafeed, Interval
from custom_pandas_data import CustomPandasData

class TradingViewData:
    """
    A class to handle downloading, saving, and loading stock data using TradingView.
    """

    def __init__(self, max_years=5, tv_user=None, tv_password=None):
        """
        Initialize the TradingViewData class.

        Parameters:
        max_years (int): The maximum number of years of historical data to download.
        """
        self.max_years = max_years
        if tv_user and tv_password:
            self.tv = TvDatafeed(username=tv_user, password=tv_password)    
        else:
            self.tv = TvDatafeed()

    def refresh_data(self, ticker, exchange):
        """
        Refresh the investment daily price data for a given ticker. If the data is already downloaded,
        it will be updated with the latest data. If not, it will download the past max_years of data.

        Parameters:
        ticker (str): The stock ticker symbol.
        exchange (str): The exchange where the stock is listed.

        Returns:
        pd.DataFrame: The refreshed investment data.
        """
        # Check if the data is already downloaded
        filename = f"{ticker.lower()}_data.csv"
        daily_price_data = None
        if not os.path.exists(filename):
            # Download the past max_years of data
            today = datetime.today().strftime('%Y-%m-%d')
            start = (datetime.today() - relativedelta(years=self.max_years)).strftime('%Y-%m-%d')
            daily_price_data = self.download_and_save_csv(ticker=ticker, exchange=exchange, start=start, end=today, filename=filename, savefile=True)
        else:
            # Load existing data and update with the latest data
            existing_data = pd.read_csv(filename, parse_dates=['datetime'])
            last_date = existing_data['datetime'].max().date()
            today = datetime.today().date()
            if last_date < today:
                start = last_date.strftime('%Y-%m-%d')
                end = today.strftime('%Y-%m-%d')
                stock_data = self.download_and_save_csv(ticker=ticker, exchange=exchange, start=start, end=end, filename=filename, savefile=False)
                
                if stock_data is None or stock_data.empty:
                    return existing_data
                
                # Combine existing data with new data
                daily_price_data = pd.concat([existing_data, stock_data]).drop_duplicates(subset=['datetime']).sort_values(by='datetime')
                daily_price_data.to_csv(filename, index=False)

        return daily_price_data

    def download_and_save_csv(self, ticker, exchange, start, end, filename, savefile=False):
        """
        Download stock data using TradingView and save it to a CSV file.

        Parameters:
        ticker (str): The stock ticker symbol.
        exchange (str): The exchange where the stock is listed.
        start (str): The start date for the data download (YYYY-MM-DD).
        end (str): The end date for the data download (YYYY-MM-DD).
        filename (str): The name of the CSV file to save the data.
        savefile (bool): Whether to save the data to a CSV file.

        Returns:
        pd.DataFrame: The downloaded stock data.
        """
        # Download data
        n_days = self.calculate_days_between(start, end)
        if n_days <= 0:
            return None
        
        if n_days <= 365:
            bars = n_days
        else:
            bars = int(n_days / 365) * 5 * 52

        stock_data = self.tv.get_hist(ticker, exchange, interval=Interval.in_daily, n_bars=bars)
        stock_data = stock_data[(stock_data.index >= start) & (stock_data.index <= end)]

        stock_data['openinterest'] = 0  # Set open interest to 0 (not used in equities)
        stock_data['sec_code'] = ticker  # Add security code (ticker)

        # Rename columns to match backtrader expected format
        stock_data.rename(columns={'open': 'open', 'high': 'high', 'low': 'low',
                                   'close': 'close', 'volume': 'volume'}, inplace=True)

        # Convert DatetimeIndex to a column
        stock_data = stock_data.reset_index().rename(columns={'index': 'datetime'})
        stock_data['datetime'] = pd.to_datetime(stock_data['datetime'])  # Ensure datetime is in correct format
        # Select columns in required order
        stock_data = stock_data[['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest', 'sec_code']]

        # Append to CSV if it exists, otherwise create a new file
        if savefile:
            if os.path.exists(filename):
                existing_data = pd.read_csv(filename, parse_dates=['datetime'])
                combined_data = pd.concat([existing_data, stock_data]).drop_duplicates(subset=['datetime']).sort_values(by='datetime')
                combined_data.to_csv(filename, index=False)
            else:
                stock_data.to_csv(filename, index=False)
            print(f"Price data saved to {filename}")
        stock_data.set_index('datetime', inplace=True)
        return stock_data

    def load_data_from_csv(self, ticker):
        """
        Load stock data from a CSV file.

        Parameters:
        ticker (str): The stock ticker symbol.

        Returns:
        pd.DataFrame: The loaded stock data.
        """
        filename = f"{ticker.lower()}_data.csv"
        # Read CSV to pandas DataFrame
        data = pd.read_csv(filename, parse_dates=['datetime'])
        data.set_index('datetime', inplace=True)
        return data

    def fetch_realtime_1hour_data(self, ticker, exchange, hours=24):
        """
        Fetch real-time 1-hour stock pricing data from TradingView.

        Parameters:
        ticker (str): The stock ticker symbol.
        exchange (str): The exchange where the stock is listed.

        Returns:
        pd.DataFrame: The real-time 1-hour stock pricing data.
        """
        # Fetch real-time 1-hour data
        stock_data = self.tv.get_hist(ticker, exchange, interval=Interval.in_1_hour, n_bars=hours, extended_session=True)
        stock_data['openinterest'] = 0  # Set open interest to 0 (not used in equities)
        stock_data['sec_code'] = ticker  # Add security code (ticker)

        # Rename columns to match backtrader expected format
        stock_data.rename(columns={'open': 'open', 'high': 'high', 'low': 'low',
                                   'close': 'close', 'volume': 'volume'}, inplace=True)

        # Convert DatetimeIndex to a column
        stock_data = stock_data.reset_index().rename(columns={'index': 'datetime'})
        stock_data['datetime'] = pd.to_datetime(stock_data['datetime'])  # Ensure datetime is in correct format
        # Select columns in required order
        stock_data = stock_data[['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest', 'sec_code']]
        stock_data.set_index('datetime', inplace=True)
        return stock_data
    
    def calculate_days_between(self, start_date, end_date):
        """
        Calculate the number of days between two dates.

        Parameters:
        start_date (str): The start date in the format 'YYYY-MM-DD'.
        end_date (str): The end date in the format 'YYYY-MM-DD'.

        Returns:
        int: The number of days between the start and end dates.
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        delta = end - start
        return delta.days
      
if __name__ == "__main__":
    tvd = TradingViewData()
    # Download and save data
    ticker = "AAPL"
    exchange = "NASDAQ"
    
    daily_price_data = tvd.refresh_data(ticker, exchange)
    # Ensure the datetime column is in datetime format
    daily_price_data['datetime'] = pd.to_datetime(daily_price_data['datetime'])
    print(daily_price_data)

    # Read data from CSV
    daily_price_data = tvd.load_data_from_csv(ticker)

    # Create Backtrader PandasData feed
    data_feed = CustomPandasData(dataname=daily_price_data)
    print(data_feed)

    # Fetch real-time 1-hour data
    realtime_data = tvd.fetch_realtime_1hour_data(ticker, exchange, 48)
    print(realtime_data)