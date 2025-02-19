import yfinance as yf
import pandas as pd
import backtrader as bt
from datetime import datetime
import osgf_strategy as osgf
from sma_strategy import SMAStrategy
from key_Indicator_analyzer import KeyIndicatorAnalyzer
from trade_list_analyzer import TradeListAnalyzer
from dotenv import load_dotenv
import os
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
#logger.warning("Its a Warning")
#logger.error("Error logging")
#logger.critical("Critical logging")

# Step 1: Download NVDA daily stock data using yfinance
def download_and_save_csv(ticker="NVDA", start="2022-01-01", end="2025-02-19", filename="nvda_data.csv", savefile=False):
    # Download data
    stock_data = yf.download(ticker, start=start, end=end, interval='1d')

    # Check for multi-index columns and flatten them
    if isinstance(stock_data.columns, pd.MultiIndex):
        stock_data.columns = [col[0] for col in stock_data.columns]  # Take the first level ('Close', 'Open', etc.)

    stock_data['sec_code'] = ticker  # Add security code (ticker)
    stock_data['openinterest'] = 0  # Set open interest to 0 (not used in equities)
    
    # Rename columns to match backtrader expected format
    stock_data.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 
                               'Close': 'close', 'Volume': 'volume'}, inplace=True)
    
    #stock_data.reset_index(inplace=True)  # Ensure Date is a regular column
    # Convert DatetimeIndex to a column
    stock_data['datetime'] = stock_data.index
    # Select columns in required order
    stock_data = stock_data[['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest', 'sec_code']]
    
    #stock_data.rename(columns={'Datetime': 'datetime'}, inplace=True)
    #stock_data.set_index('datetime', inplace=True)
    # Save to CSV
    if(savefile):
        stock_data.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    return stock_data


# Step 2: Read CSV using pandas
def load_data_from_csv(filename="nvda_data.csv"):
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
    # Key Indicator Analyzer
    cerebro.addanalyzer(KeyIndicatorAnalyzer, _name='key_indicator_analyzer')   
    # Trade List Analyzer
    cerebro.addanalyzer(TradeListAnalyzer, _name='trade_list_analyzer') 

# Step 6: Get the analyzer results
def get_my_analyzer(result,cerebro):
    analyzer = {}
    # 返回参数
    #analyzer['period1'] = result.params.period1
    #analyzer['period2'] = result.params.period2
    # 提取年化收益
    analyzer['年化收益率'] = result.analyzers._Returns.get_analysis()['rnorm']
    analyzer['年化收益率（%）'] = result.analyzers._Returns.get_analysis()['rnorm100']
    # 提取最大回撤(习惯用负的做大回撤，所以加了负号)
    analyzer['最大回撤（%）'] = result.analyzers._DrawDown.get_analysis()['max']['drawdown'] * (-1)
    # 提取夏普比率
    analyzer['年化夏普比率'] = result.analyzers._SharpeRatio_A.get_analysis()['sharperatio']
    # Get trade list analyzer
    trade_list_df, trade_dict = result.analyzers.trade_list_analyzer.get_analysis()
    analyzer['交易股票列表'] = trade_list_df
    analyzer['交易股票买卖日期'] = trade_dict
    
    # Dowload benchmark data
    benchmark_data = download_and_save_csv("SPY")
    #benchmark_data = load_data_from_csv("spy_data.csv")
    # Get key indicator analyzer
    key_indicator_df, daily_details_dict = result.analyzers.key_indicator_analyzer.get_analysis_data(benchmark_data, 'SPY')
    analyzer['重要指标'] = key_indicator_df
    analyzer['每日详情'] = daily_details_dict
    return analyzer

TIMEFRAMES = {
    None: None,
    'days': bt.TimeFrame.Days,
    'weeks': bt.TimeFrame.Weeks,
    'months': bt.TimeFrame.Months,
    'years': bt.TimeFrame.Years,
    'notimeframe': bt.TimeFrame.NoTimeFrame,
}

# Step 6: Run the backtest
def run_backtest():
    # Load environment variables from .env file
    load_dotenv()

    # Access environment variables
    api_key = os.getenv('API_KEY')
    secret_key = os.getenv('SECRET_KEY')

    print(f"API_KEY: {api_key}")
    print(f"SECRET_KEY: {secret_key}")
    
    # Download and save data
    ticker = "HIMS"
    filename = f"{ticker.lower()}_data.csv"
    daily_price_data = download_and_save_csv(ticker = ticker, start="2022-01-01", end="2025-02-19",filename=filename, savefile=True)

    # Read data from CSV
    daily_price_data = load_data_from_csv(filename)

    # Create Backtrader PandasData feed
    data_feed = CustomPandasData(dataname=daily_price_data) 
    # Create Cerebro instance
    cerebro = bt.Cerebro()
    #cerebro.addstrategy(SMAStrategy, short_period=5, long_period=10)  # Add the test strategy
    # add optimizer of strategy
    cerebro.optstrategy(SMAStrategy, short_period=range(3, 6, 1), long_period=range(10, 21, 10))

    # Add data feed
    cerebro.adddata(data_feed, name = ticker)  # Add NVDA data
    
    cerebro.broker.set_cash(100000.0)  # Initial cash
    cerebro.broker.setcommission(commission=0.001)  # Commission for trades

    add_analyzers(cerebro)  # Add analyzers
    # Print starting cash
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():,.2f}")

    # Run backtest
    result = cerebro.run(tradehistory=True,maxcpus=1)

    # Print final cash
    print(f"Final Portfolio Value: ${cerebro.broker.getvalue():,.2f}")

    ret = []
    for i, res in enumerate(result):
        ret.append(get_my_analyzer(res[0], cerebro))
        print("--------------- analyzers -----------------")
        print(ret[i])
        
    pd.DataFrame(ret).to_csv('result.csv', index=False)

    # Plot the results
    cerebro.plot()

if __name__ == "__main__":
    run_backtest()
