import yfinance as yf
import pandas as pd
import backtrader as bt
from datetime import datetime
from dotenv import load_dotenv
import os

class YFinanceData:
    def __init__(self, max_years=5):
        self.max_years = max_years

    def refresh_investment_data(self, ticker):
        # Check if the data is already downloaded
        # If not, download the past 5 years data
        filename = f"{ticker.lower()}_data.csv"
        daily_price_data = None
        if not os.path.exists(filename):
            today = datetime.today().strftime('%Y-%m-%d')
            start = (datetime.today() - pd.DateOffset(years=self.max_years)).strftime('%Y-%m-%d')
            daily_price_data =self.download_and_save_csv(ticker = ticker, start = start, end=today,filename=filename, savefile=True)
        else:
            existing_data = pd.read_csv(filename, parse_dates=['datetime'])
            last_date = existing_data['datetime'].max()
            today = datetime.today()
            if last_date < today:
                start = last_date + pd.DateOffset(days=1)
                stock_data = self.download_and_save_csv(ticker = ticker, start = start, end=today,filename=filename, savefile=False)

                # Combine existing data with new data
                daily_price_data = pd.concat([existing_data, stock_data]).drop_duplicates(subset=['datetime']).sort_values(by='datetime')
                daily_price_data.to_csv(filename, index=False)

        return daily_price_data

    # Step 1: Download Stock daily price data using yfinance
    def download_and_save_csv(self, ticker, start, end, filename, savefile=False):
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
        
        #stock_data.set_index('datetime', inplace=True)
        # Save to CSV
        if(savefile):
            stock_data.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
        return stock_data


    # Step 2: Read CSV using pandas
    def load_data_from_csv(self, ticker):
        filename = f"{ticker.lower()}_data.csv"
        # Read CSV to pandas DataFrame
        data = pd.read_csv(filename, parse_dates=['datetime'])
        data.set_index('datetime', inplace=True)
        return data

# Step 3: Custom Pandas Data Feed for Backtrader
class CustomPandasData(bt.feeds.PandasData):
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', 'openinterest'),
        ('ticker','sec_code'),
    )


if __name__ == "__main__":
    yfd = YFinanceData()
    # Download and save data
    ticker = "HIMS"
    #daily_price_data = yfd.refresh_investment_data(ticker)

    # Read data from CSV
    daily_price_data = yfd.load_data_from_csv(ticker)

    # Create Backtrader PandasData feed
    data_feed = CustomPandasData(dataname=daily_price_data) 
    print(data_feed)
