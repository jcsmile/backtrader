import yfinance as yf
import pandas as pd
import backtrader as bt
from datetime import datetime
from dotenv import load_dotenv
import os
from data.custom_pandas_data import CustomPandasData

class YFinanceData:
    """
    A class to handle downloading, saving, and loading stock data using yfinance.
    """
    def __init__(self, max_years=5):
        """
        Initialize the YFinanceData class.

        Parameters:
        max_years (int): The maximum number of years of historical data to download.
        """
        self.max_years = max_years

    def refresh_data(self, ticker):
        """
        Refresh the investment daily price data for a given ticker. If the data is already downloaded,
        it will be updated with the latest data. If not, it will download the past max_years of data.

        Parameters:
        ticker (str): The stock ticker symbol.

        Returns:
        pd.DataFrame: The refreshed investment data.
        """        
        # Check if the data is already downloaded
        # If not, download the past max_years of data
        filename = f"{ticker.lower()}_data.csv"
        daily_price_data = None
        if not os.path.exists(filename):
            # Download the past max_years of data
            today = datetime.today().strftime('%Y-%m-%d')
            start = (datetime.today() - pd.DateOffset(years=self.max_years)).strftime('%Y-%m-%d')
            daily_price_data =self.download_and_save_csv(ticker = ticker, start = start, end=today,filename=filename, savefile=True)
        else:
            # Load existing data and update with the latest data
            existing_data = pd.read_csv(filename, parse_dates=['datetime'])
            last_date = existing_data['datetime'].max().date()
            today = datetime.today().date()
            if last_date < today:
                start = (last_date + pd.DateOffset(days=1)).strftime('%Y-%m-%d')
                stock_data = self.download_and_save_csv(ticker = ticker, start = start, end=today.strftime('%Y-%m-%d'),filename=filename, savefile=False)

                # Combine existing data with new data
                daily_price_data = pd.concat([existing_data, stock_data]).drop_duplicates(subset=['datetime']).sort_values(by='datetime')
                daily_price_data.to_csv(filename, index=False)
                daily_price_data.set_index('datetime', inplace=True)
        return daily_price_data

    # Step 1: Download Stock daily price data using yfinance
    def download_and_save_csv(self, ticker, start, end, filename, savefile=False):
        """
        Download stock data using yfinance and save it to a CSV file.

        Parameters:
        ticker (str): The stock ticker symbol.
        start (str): The start date for the data download (YYYY-MM-DD).
        end (str): The end date for the data download (YYYY-MM-DD).
        filename (str): The name of the CSV file to save the data.
        savefile (bool): Whether to save the data to a CSV file.

        Returns:
        pd.DataFrame: The downloaded stock data.
        """       
        # Download data
        stock_data = yf.download(ticker, start=start, end=end, interval='1d')

        # Check for multi-index columns and flatten them
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_data.columns = [col[0] for col in stock_data.columns]  # Take the first level ('Close', 'Open', etc.)
    
        stock_data['openinterest'] = 0  # Set open interest to 0 (not used in equities)
        stock_data['sec_code'] = ticker  # Add security code (ticker)
        
        # Rename columns to match backtrader expected format
        stock_data.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 
                                'Close': 'close', 'Volume': 'volume'}, inplace=True)
        
        # Convert DatetimeIndex to a column
        stock_data['datetime'] = stock_data.index
        # Select columns in required order
        stock_data = stock_data[['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest', 'sec_code']]
        stock_data.set_index('datetime', inplace=True)
        # Append to CSV if it exists, otherwise create a new file
        if savefile:
            if os.path.exists(filename):
                existing_data = pd.read_csv(filename, parse_dates=['datetime'])
                combined_data = pd.concat([existing_data, stock_data]).drop_duplicates(subset=['datetime']).sort_values(by='datetime')
                combined_data.to_csv(filename, index=False)
            else:
                stock_data.to_csv(filename, index=False)
            print(f"Price data saved to {filename}")
        return stock_data


    # Step 2: Read CSV using pandas
    def load_data_from_csv(self, ticker):
        filename = f"{ticker.lower()}_data.csv"
        # Read CSV to pandas DataFrame
        data = pd.read_csv(filename, parse_dates=['datetime'])
        data.set_index('datetime', inplace=True)
        return data

if __name__ == "__main__":
    yfd = YFinanceData()
    # Download and save data
    ticker = "HIMS"
    daily_price_data = yfd.refresh_data(ticker)

    # Read data from CSV
    daily_price_data = yfd.load_data_from_csv(ticker)

    # Create Backtrader PandasData feed
    data_feed = CustomPandasData(dataname=daily_price_data) 
    print(data_feed)
