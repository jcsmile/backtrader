import backtrader as bt
from indicators.volume_indicator import VolumeIndicator
import logging

class VolumeStrategy(bt.Strategy):
    def __init__(self):
        self.volume_indicator = VolumeIndicator()
        self.logger = logging.getLogger()
        self.order = None

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        self.logger.info('{}, {}'.format(dt.isoformat(), txt))

    def next(self):
        volume_label = self.volume_indicator.lines.volume_label[0]
        if self.order:
            return
        # 是否已经买入
        if not self.position:
            shares = self.broker.getcash() * 0.90 // self.datas[0].close[0]
            
            if volume_label == 1:
                print(f"High volume detected on {self.data.datetime.date(0)}")
                self.order = self.buy(size=shares)
        
        else:
            if volume_label == -1:
                print(f"Low volume detected on {self.data.datetime.date(0)}")
                self.order = self.sell(size=self.position.size)
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