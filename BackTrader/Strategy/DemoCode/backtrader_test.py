import backtrader as bt 
import os
from pathlib import Path 
import datetime
import pandas as pd

class TestStrategy(bt.Strategy):
    params = (('maperiod', 15), )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("Buy Executed {}".format (order.executed.price))
            elif order.issell ():
                self.log("Sell Executed {}".format (order.executed.price))
                self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
            self.order = None


    def next (self):
        self.log("Close {}".format(self.dataclose[0]))
        if self.order:
            return
        if not self.position:
            if self.dataclose [0] > self.sma[0]:
                self.log("Buy Create {}".format (self.dataclose[0]))
                self.order=self.buy()
        else:
            if self.dataclose[0] < self.sma[0]:
                self.log("Sell Create {}".format (self.dataclose[0]))
                self.order = self.sell()
    def log(self, txt):
        dt = self.datas [0].datetime.date(0) 
        print ("{}{}".format (dt.isoformat(), txt))

    def stop(self):
        print(self.params.maperiod, self.broker.getvalue())

if __name__ =='__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(10000000)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.addstrategy(TestStrategy)
    #cerebro.optstrategy(TestStrategy, maperiod=range(10, 31))
    pathfile = "C:\Data\Quantitative\BackTrader\BTCUSDT_15m_20230623.csv"
    df = pd.DataFrame(pd.read_csv(pathfile, delimiter=",", index_col="Datetime", parse_dates= True))

    df.index = pd.to_datetime(df.index,format="%Y-%m-%d",utc=True)
    #data = bt.feeds.PandasData(dataname=df)
    data = bt.feeds.PandasData(dataname=df, fromdate=datetime.datetime(2021, 1, 1), todate=datetime.datetime(2021, 3, 31))
    cerebro.adddata(data)
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=15)
    print('Starting Portfolio Value: {}'.format(cerebro.broker.getvalue()))
    cerebro.run()
    #print('Final Portfolio Value: {}'.format(cerebro.broker.getvalue()))
    cerebro.plot(style='candlestick')
