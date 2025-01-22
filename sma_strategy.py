import logging
import backtrader as bt
import numpy as np

# Creating an object
logger = logging.getLogger()
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
