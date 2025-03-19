import yfinance as yf
import pandas as pd
import backtrader as bt
from datetime import datetime
import strategies.osgf_strategy as osgf
from strategies.sma_strategy import SMAStrategy
from strategies.volume_strategy import VolumeStrategy
from strategies.custom_strategy import CustomStrategy
from analyzers.key_Indicator_analyzer import KeyIndicatorAnalyzer
from analyzers.trade_list_analyzer import TradeListAnalyzer
from dotenv import load_dotenv
import os
import logging
from data.source_data import SourceData
from data.yfinanceData import YFinanceData
from data.tradingviewData import TradingViewData
from data.custom_pandas_data import CustomPandasData
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('TkAgg') 
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
    #cerebro.addanalyzer(KeyIndicatorAnalyzer, _name='key_indicator_analyzer')   
    # Trade List Analyzer
    #cerebro.addanalyzer(TradeListAnalyzer, _name='trade_list_analyzer') 

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
    #trade_list_df, trade_dict = result.analyzers.trade_list_analyzer.get_analysis()
    #analyzer['交易股票列表'] = trade_list_df
    #analyzer['交易股票买卖日期'] = trade_dict
    
    # Dowload benchmark data
    #benchmark_data = download_and_save_csv("SPY")
    #benchmark_data = load_data_from_csv("spy_data.csv")
    # Get key indicator analyzer
    #key_indicator_df, daily_details_dict = cerebro.analyzers.key_indicator_analyzer.get_analysis_data(benchmark_data, 'SPY')
    #analyzer['重要指标'] = key_indicator_df
    #analyzer['每日详情'] = daily_details_dict
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
    
    yfd = YFinanceData()
    tv = TradingViewData()   
    ticker = "AAPL"
    exchange = "NYSE"
    daily_price_data = yfd.refresh_data(ticker)
    #daily_price_data = yfd.load_data_from_csv(ticker)
    # Ensure the datetime column is in datetime format
    #daily_price_data['datetime'] = pd.to_datetime(daily_price_data['datetime'])
    # Create Backtrader PandasData feed
    data_feed = CustomPandasData(dataname=daily_price_data) 
    # Create Cerebro instance
    cerebro = bt.Cerebro()
    # Add the test strategy
    cerebro.addstrategy(SMAStrategy, short_period=5, long_period=10)
    #cerebro.addstrategy(VolumeStrategy) 
    # add optimizer of strategy
    #cerebro.optstrategy(SMAStrategy, short_period=range(3, 6, 1), long_period=range(10, 21, 10))

    # Add data feed
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

    ret = []
    for i, res in enumerate(result):
        ret.append(get_my_analyzer(res, cerebro))
        print("--------------- analyzers -----------------")
        print(ret[i])
        
    pd.DataFrame(ret).to_csv('result.csv', index=False)

    # Plot the results
    cerebro.plot()

STRATEGY_CLASSES = {
    "SMAStrategy": SMAStrategy,
    "VolumeStrategy": VolumeStrategy,
    "CustomStrategy": CustomStrategy,
}

class Backtest:
    def __init__(self, source_data, cash=100000, commission=1 / 1000, slip_type=-1, slip_value=0, IS_ALL_IN=False,
                 params_dict={}, make_plot=True):
        self.source_data = source_data
        self.cash = cash
        self.commission = commission
        self.slip_type = slip_type
        self.slip_value = slip_value
        self.IS_ALL_IN = IS_ALL_IN
        self.params_dict = params_dict
        self.make_plot = make_plot
        self.origin_cash = 0
        self.cls_ret = {}   

    def fetch_data(self, ticker, exchange):
        daily_price_data = self.source_data.refresh_data(ticker, exchange)
        data_feed = CustomPandasData(dataname=daily_price_data)
        return data_feed
    
    def run(self, ticker, exchange):
        strategy_params = self.params_dict.get("strategy_params", {})
        analyzer_params = self.params_dict.get('analyzers', {})
        plot_params = self.params_dict.get("plot", {})
        strategy_class_name = self.params_dict.get('strategy_class', "SMAStrategy")  # Default to SMAStrategy if not provided
        strategy_class = STRATEGY_CLASSES.get(strategy_class_name)  # Retrieve the class reference
        if strategy_class is None:
            raise ValueError(f"Invalid strategy class name: {strategy_class_name}")
                
        datas = self.fetch_data(ticker, exchange)
        cerebro = bt.Cerebro(cheat_on_open=self.IS_ALL_IN)
        cerebro.addstrategy(strategy_class, **strategy_params)
        #cerebro.addstrategy(SMAStrategy, short_period=5, long_period=10)

        if isinstance(datas, list):
            for item in datas:
                cerebro.adddata(item)
        else:
            cerebro.adddata(datas, name=ticker)

        cerebro.broker.setcash(self.cash)
        cerebro.broker.setcommission(self.commission)

        if self.slip_type == 0:
            cerebro.broker.set_slippage_fixed(self.slip_value)
        elif self.slip_type == 1:
            cerebro.broker.set_slippage_perc(self.slip_value)

        for ana_name, ana_class in analyzer_params.items():
            cerebro.addanalyzer(ana_class, _name=ana_name)

        back_ret = cerebro.run()

        if self.make_plot:
            cerebro.plot(**plot_params) 
            plt.show()  # 添加这一行以确保图像窗口保持打开状态
        return back_ret, cerebro
    
if __name__ == "__main__":
    #run_backtest()



    tv_data = TradingViewData()
    tester = Backtest(tv_data, cash=100000, commission=1 / 1000, slip_type=-1, slip_value=0, IS_ALL_IN=False,
                    params_dict={"strategy_params": {"short_period": 5, "long_period": 10},
                                 "strategy_class": "SMAStrategy",
                                    'analyzers': {'sharp': bt.analyzers.SharpeRatio,
                                                    'annual_return': bt.analyzers.AnnualReturn,
                                                    'drawdown': bt.analyzers.DrawDown}})
    ret, cere = tester.run("AAPL", "NASDAQ")
    print('Sharpe Ratio: ', ret[0].analyzers.sharp.get_analysis())
    print('drawdown: ', ret[0].analyzers.drawdown.get_analysis())
    #cere.plot(style='candle')
    input("Press Enter to continue...")
