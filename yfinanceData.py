import yfinance as yf
import pandas as pd
import backtrader as bt
from datetime import datetime

# Step 1: Download NVDA daily stock data using yfinance
def download_and_save_csv(ticker="NVDA", start="2022-01-01", end="2025-01-01", filename="nvda_data.csv"):
    # Download data
    stock_data = yf.download(ticker, start=start, end=end, interval='1d')

    # Check for multi-index columns and flatten them
    if isinstance(stock_data.columns, pd.MultiIndex):
        stock_data.columns = [col[0] for col in stock_data.columns]  # Take the first level ('Close', 'Open', etc.)

    stock_data.reset_index(inplace=True)  # Ensure Date is a regular column
    stock_data['sec_code'] = ticker  # Add security code (ticker)
    stock_data['openinterest'] = 0  # Set open interest to 0 (not used in equities)
    
    # Rename columns to match backtrader expected format
    stock_data.rename(columns={'Date': 'datetime', 'Open': 'open', 'High': 'high', 'Low': 'low', 
                               'Close': 'close', 'Volume': 'volume'}, inplace=True)
    
    # Select columns in required order
    stock_data = stock_data[['datetime', 'sec_code', 'open', 'high', 'low', 'close', 'volume', 'openinterest']]
    
    # Save to CSV
    stock_data.to_csv(filename, index=False)
    print(f"Data saved to {filename}")


# Step 2: Read CSV using pandas
def load_data_from_csv(filename="nvda_data.csv"):
    # Read CSV to pandas DataFrame
    data = pd.read_csv(filename, parse_dates=['datetime'])
    return data

# Step 3: Custom Pandas Data Feed for Backtrader
class CustomPandasData(bt.feeds.PandasData):
    params = (
        ('datetime', 'datetime'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', 'openinterest'),
    )

# Step 4: Backtest Strategy
class TestStrategy(bt.Strategy):
    def __init__(self):
        self.sma = bt.indicators.SimpleMovingAverage(period=20)  # 20-day SMA

    def next(self):
        if self.data.close[0] > self.sma[0]:
            self.buy(size=10)
        elif self.data.close[0] < self.sma[0]:
            self.sell(size=10)

# Step 5: Run the backtest
def run_backtest(filename="nvda_data.csv"):
    # Download and save data
    download_and_save_csv()

    # Read data from CSV
    data = load_data_from_csv(filename)

    # Create Backtrader PandasData feed
    data_feed = CustomPandasData(dataname=data)

    # Create Cerebro instance
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy)  # Add the test strategy
    cerebro.adddata(data_feed)  # Add NVDA data
    cerebro.broker.set_cash(100000.0)  # Initial cash
    cerebro.broker.setcommission(commission=0.001)  # Commission for trades

    # Print starting cash
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():,.2f}")

    # Run backtest
    cerebro.run()

    # Print final cash
    print(f"Final Portfolio Value: ${cerebro.broker.getvalue():,.2f}")

    # Plot the results
    cerebro.plot()

if __name__ == "__main__":
    run_backtest()
