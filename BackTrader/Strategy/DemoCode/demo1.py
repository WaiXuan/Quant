import backtrader as bt
import os
from pathlib import Path
import datetime
import pandas as pd


class TestStrategy(bt.Strategy):

    def __init__(self):
        self.bt_sma30 = bt.indicators.MovingAverageSimple(self.data, period=30)
        self.bt_sma15 = bt.indicators.MovingAverageSimple(self.data, period=15)
        self.bt_sma10 = bt.indicators.MovingAverageSimple(self.data, period=10)
        self.bt_sma5 = bt.indicators.MovingAverageSimple(self.data, period=5)
        
        # 前面Line穿越後面Line = 1
        self.buy_sell_signal = bt.indicators.CrossOver(self.data.close, self.bt_sma30)
        
    def prenext(self):
        print("Not mature enough ...")
    
    def nextstart(self):
        print("Rites of passage")
    
    def next(self):
        print("A new bar datetime :" + str(self.data.datetime.datetime())+" close :"+ str(self.data.close[0]))
        ma_value = self.bt_sma30[0]
        pre_ma_value = self.bt_sma30[-1]
        
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
        # if self.data.close[0] > ma_value and self.data.close[-1] <= pre_ma_value:
        #     print("Buy signal")
        #     self.buy()
        # elif self.data.close[0] < ma_value and self.data.close[-1] >= pre_ma_value:
        #     print("Sell signal")
        #     self.sell()
        
        
        
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
