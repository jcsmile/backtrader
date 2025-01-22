import yfinance as yf
import pandas as pd
import backtrader as bt
from datetime import datetime
import osgf_strategy as osgf
from sma_strategy import SMAStrategy

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
#from osgf_strategy import OsgfStrategy
#from sma_strategy import SMAStrategy

# Step 5: Add analyzer
def add_analyzers(cerebro):
    # 添加分析指标
    # 返回年初至年末的年度收益率
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn')
    # 计算最大回撤相关指标
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown')
    # 计算年化收益：日度收益
    cerebro.addanalyzer(bt.analyzers.Returns, _name='_Returns', tann=252)
    # 计算年化夏普比率：日度收益
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio', timeframe=bt.TimeFrame.Days, annualize=True, riskfreerate=0) # 计算夏普比率
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='_SharpeRatio_A')
    # 返回收益率时序
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')

# Step 6: Run the backtest
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

    add_analyzers(cerebro)  # Add analyzers
    # Print starting cash
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():,.2f}")

    # Run backtest
    result = cerebro.run()

    # Print final cash
    print(f"Final Portfolio Value: ${cerebro.broker.getvalue():,.2f}")

    # Print Analyzers
    print("--------------- AnnualReturn -----------------")
    print(result[0].analyzers._AnnualReturn.get_analysis())
    print("--------------- DrawDown -----------------")
    print(result[0].analyzers._DrawDown.get_analysis())
    print("--------------- Returns -----------------")
    print(result[0].analyzers._Returns.get_analysis())
    print("--------------- SharpeRatio -----------------")
    print(result[0].analyzers._SharpeRatio.get_analysis())
    print("--------------- SharpeRatio_A -----------------")
    print(result[0].analyzers._SharpeRatio_A.get_analysis())

    # 常用指标提取
    analyzer = {}
    # 提取年化收益
    analyzer['年化收益率'] = result[0].analyzers._Returns.get_analysis()['rnorm']
    analyzer['年化收益率（%）'] = result[0].analyzers._Returns.get_analysis()['rnorm100']
    # 提取最大回撤
    analyzer['最大回撤（%）'] = result[0].analyzers._DrawDown.get_analysis()['max']['drawdown'] * (-1)
    # 提取夏普比率
    analyzer['年化夏普比率'] = result[0].analyzers._SharpeRatio_A.get_analysis()['sharperatio']
    print("--------------- analyzers -----------------")
    print(analyzer)

    # Daily return series
    ret = pd.Series(result[0].analyzers._TimeReturn.get_analysis())
    # Plot the results
    cerebro.plot()

if __name__ == "__main__":
    run_backtest()
