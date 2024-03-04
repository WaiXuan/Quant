import backtrader as bt
import os
from pathlib import Path
import datetime
import pandas as pd

class three_bars(bt.Indicator):
    lines = ('up', 'down')
    
    def __init__(self):
        #策略開始最小週期
        self.addminperiod(4)
        #畫進主圖
        self.plotinfo.plotmaster = self.data
        
    def next(self):
        self.up[0] = max(max(self.data.close.get(ago=-1, size=3)), max(self.data.open.get(ago=-1, size=3)))
        self.down[0] = min(min(self.data.close.get(ago=-1, size=3)), min(self.data.open.get(ago=-1, size=3)))
        # self.lines.up = bt.indicators.Highest(self.data.high, period=3)
        # self.lines.down = bt.indicators.Lowest(self.data.low, period=3)


class TestStrategy(bt.Strategy):

    def __init__(self):
        self.up_down = three_bars(self.data)
        self.buy_signal = bt.indicators.CrossOver(self.data.close, self.up_down.up)
        self.sell_signal = bt.indicators.CrossDown(self.data.close, self.up_down.down)   
        self.buy_signal.plotinfo.plot = False
        self.sell_signal.plotinfo.plot = False
        
        
    def prenext(self):
        print("Not mature enough ...")
    
    def nextstart(self):
        print("Rites of passage")
    
    def next(self):
        print("A new bar datetime :" + str(self.data.datetime.datetime())+" close :"+ str(self.data.close[0]))
        
        if not self.position and self.buy_signal[0] == 1:
            self.order = self.buy()          
        if not self.position and self.sell_signal[0] == 1:
            self.order = self.sell() 
            
        if self.getposition().size < 0 and self.buy_signal[0] == 1:
            self.order = self.close()
            self.order = self.buy()
        if self.getposition().size > 0 and self.sell_signal[0] == 1:
            self.order = self.close()
            self.order = self.sell()
        
    def stop(self):
        print("ending")
    


if __name__ == "__main__":
    # 1. Create a Cerebro entity
    cerebro = bt.Cerebro()

    # 2. Add data feed
    # 2.1 Create a data feed
    pathfile = "C:\Data\Quantitative\BackTrader\BTCUSDT_15m_20230623.csv"
    df = pd.DataFrame(
        pd.read_csv(pathfile, delimiter=",", index_col="Datetime", parse_dates=True)
    )

    df.index = pd.to_datetime(df.index, format="%Y-%m-%d", utc=True)
    data = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime.datetime(2021, 2, 28),
        todate=datetime.datetime(2021, 4, 3),
    )
    
    cerebro.adddata(data)
    #cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=15)
    print("Starting Portfolio Value: {}".format(cerebro.broker.getvalue()))

    # 3. Add strategy
    cerebro.addstrategy(TestStrategy)
    # cerebro.optstrategy(TestStrategy, maperiod=range(10, 31))
    
    # 4. Run the strategy
    cerebro.run()
    # print('Final Portfolio Value: {}'.format(cerebro.broker.getvalue()))
    
    # 5. Plot the result
    cerebro.plot(style="candlestick")
