import logging
import backtrader as bt
import numpy as np

class SMAStrategy(bt.Strategy):
    """Two SMA Strategy
    《151 Trading Strategies》P50
    Buy when short term SMA cross above long term SMA.
    Sell When short term SMA cross down long term SMA.
    Attributes:
        sma_s: short term simple moving average, for example, 5-day SMA
        sma_l: long term simple moving average, for example, 10-day SMA
    """
    params = (('short_period', 5), ('long_period', 10))

    def __init__(self):
        self.sma_l = bt.indicators.SimpleMovingAverage(period=10)  # 10-day SMA
        self.sma_s = bt.indicators.SimpleMovingAverage(period=5)  # 5-day SMA
        self.logger = logging.getLogger()
        self.order = None
        #self.logger.info('SMAStrategy created：short_period=%d, long_period=%d' % (self.params.short_period, self.params.long_period))

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        self.logger.info('{}, {}'.format(dt.isoformat(), txt))

    def next(self):
        dt = self.datas[0].datetime.date(0)
        # If there is a pending order, do not order again, avoid duplicate orders
        if self.order:
            return
        
        current_close = self.data.close[0]
        previous_close = self.data.close[-1]  # Previous day's close price

        current_sma_s = self.sma_s[0]
        previous_sma_s = self.sma_s[-1]  # Previous day's sma_s

        current_sma_l = self.sma_l[0]
        previous_sma_l = self.sma_l[-1]  # Previous day's sma_l

        # 是否已经买入
        if not self.position:
            shares = self.broker.getcash() * 0.90 // self.datas[0].close[0]
            #shares = 100

            # Check for "Price up cross sma_s" (close price crosses above 5-day SMA) during an uptrend
            # if previous_close <= previous_sma_s and current_close >= current_sma_s and current_sma_s > current_sma_l :
            #    self.buy(size=shares)
            #    self.log(f"Price up cross Buy at {self.data.close[0]}, {shares} shares")

            # Check for "Golden Cross" (short-term SMA crosses above long_term SMA) 
            if previous_sma_s < previous_sma_l and current_sma_s >= current_sma_l:
                self.order = self.buy(size=shares)
                self.log(f"Golden Cross Buy at {self.data.close[0]}, {shares} shares")     
        else:
            # Check for "Death Cross" (short-term SMA crosses below long-term SMA)
            if previous_sma_s > previous_sma_l and current_sma_s <= current_sma_l:
                self.order = self.sell(size=self.position.size)
                self.log(f"Death Cross Sell at {self.data.close[0]}, {self.position.size} shares")


    #订单日志    
    def notify_order(self, order):
        # 未被处理的订单
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 已被处理的订单
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, ref:%.0f，Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s' %
                    (order.ref,
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm,
                     order.executed.size,
                     order.data._name))
            else:  # Sell
                self.log('SELL EXECUTED, ref:%.0f, Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s' %
                        (order.ref,
                         order.executed.price,
                         order.executed.value,
                         order.executed.comm,
                         order.executed.size,
                         order.data._name))
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order failed: %s' % order.getstatusname())
        self.order = None 