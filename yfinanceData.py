import yfinance as yf
import pandas as pd
import backtrader as bt
from datetime import datetime
import osgf_strategy as osgf

import logging
# Create and configure logger
logging.basicConfig(level=logging.INFO,
                    format='%(message)s'
                    )

# Creating an object
logger = logging.getLogger()

#logger.sethandler(logging.ConsoleHandler())
# Test messages
logger.debug("Harmless debug Message")  
logger.info("Just an information")
logger.warning("Its a Warning")
logger.error("Did you try to divide by zero")
logger.critical("Internet is down")

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
    stock_data = stock_data[['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest', 'sec_code']]
    stock_data.set_index('datetime', inplace=True)
    # Save to CSV
    #stock_data.to_csv(filename, index=False)
    #print(f"Data saved to {filename}")
    return stock_data


# Step 2: Read CSV using pandas
def load_data_from_csv(filename="nvda_data.csv"):
    # Read CSV to pandas DataFrame
    data = pd.read_csv(filename, parse_dates=['datetime'])
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

# Step 4: Backtest Strategy
class SMAStrategy(bt.Strategy):
    def __init__(self):
        self.sma20 = bt.indicators.SimpleMovingAverage(period=20)  # 20-day SMA
        self.sma5 = bt.indicators.SimpleMovingAverage(period=5)  # 5-day SMA

    def next(self):
        dt = self.datas[0].datetime.date(0)
        current_close = self.data.close[0]
        previous_close = self.data.close[-1]  # Previous day's close price

        current_sma5 = self.sma5[0]
        previous_sma5 = self.sma5[-1]  # Previous day's sma5

        current_sma20 = self.sma20[0]
        previous_sma20 = self.sma20[-1]  # Previous day's sma20

        # Check for "Price up cross SMA5" (close price crosses above 5-day SMA) during an uptrend
        if previous_close <= previous_sma5 and current_close >= current_sma5 and current_sma5 > current_sma20 :
            self.buy(size=10)
            logger.info(f"{dt}, Price up cross Buy at {self.data.close[0]}, 10 shares")
        # Check for "Golden Cross" (5-day SMA crosses above 20-day SMA) 
        elif previous_sma5 < previous_sma20 and current_sma5 >= current_sma20:
            self.buy(size=10)
            logger.info(f"{dt}, Golden Cross Buy at {self.data.close[0]}, 10 shares")     
        # Check for "Death Cross" (5-day SMA crosses below 20-day SMA)
        elif previous_sma5 > previous_sma20 and current_sma5 <= current_sma20:
            self.sell(size=10)
            logger.info(f"{dt}, Death Cross Sell at {self.data.close[0]}, 10 shares")
        # Check for "Price down cross SMA5" (close price crosses below 5-day SMA) during a downtrend
        elif previous_close > previous_sma5 and current_close <= current_sma5 and current_sma5 < current_sma20:
            self.sell(size=10)
            logger.info(f"{dt}, Price down cross Sell at {self.data.close[0]}, 10 shares")

# Step 5: Run the backtest
def run_backtest(filename="nvda_data.csv"):
    # Download and save data
    ticker = "NVDA"
    daily_price_data = download_and_save_csv(ticker)

    # Read data from CSV
    #data = load_data_from_csv(filename)

    # Create Backtrader PandasData feed
    data_feed = CustomPandasData(dataname=daily_price_data)

    # Create Cerebro instance
    cerebro = bt.Cerebro()
    cerebro.addstrategy(osgf.OsgfStrategy)  # Add the test strategy
    cerebro.adddata(data_feed, name = ticker)  # Add NVDA data
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
