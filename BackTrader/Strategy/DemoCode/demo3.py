import backtrader as bt
import os
from pathlib import Path
import datetime
import pandas as pd

class DT_Line (bt.Indicator):
    lines = ('U', 'D')
    params = (('period', 2), ('k_u', 0.7), ('k_d', 0.7))

    def __init__(self):
        self.addminperiod(self.p.period + 1)
    def next(self):
        HH = max(self.data.high.get(-1, size=self.p.period))
        LC = min(self.data.close.get (-1, size=self.p.period))
        HC = max(self.data.close.get(-1, size=self.p.period))
        LL = min(self.data.low.get(-1, size=self.p.period))
        R = max(HH - LC, HC - LL)
        self.lines.U[0] = self.data.open[0] + self.p.k_u * R
        self.lines.D[0] = self.data.open[0] - self.p.k_d * R


class TestStrategy(bt.Strategy):

    def __init__(self):
        self.dataclose = self.data0.close
        self.D_Line = DT_Line(self.data1)
        self.D_Line = self.D_Line() #調用自身將大維度映射到小維度
        self.D_Line.plotinfo.plotmaster = self.data0        
        self.data1.plotinfo.plot = False #關閉日線繪圖顯示
        
        self.buy_signal = bt.indicators.CrossOver(self.dataclose, self.D_Line.U)
        self.sell_signal = bt.indicators.CrossDown(self.dataclose, self.D_Line.D)
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
        
        # #日內交易 每日23:58平倉
        if self.data.datetime.time() >= datetime.time(23,58) and self.position:
            self.order = self.close()
        
    def stop(self):
        print("ending")
    


if __name__ == "__main__":
    # 1. Create a Cerebro entity
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(10000)
    cerebro.addsizer(bt.sizers.PercentSizer, percents = 80)
    # 2. Add data feed
    # 2.1 Create a data feed
    pathfile = "C:\Data\Quantitative\BackTrader\BTCUSDT_1m_20230623.csv"
    df = pd.DataFrame(
        pd.read_csv(pathfile, delimiter=",", index_col="Datetime", parse_dates=True)
    )

    df.index = pd.to_datetime(df.index, format="%Y-%m-%d", utc=True)
    brf_min_bar = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime.datetime(2021, 2, 28),
        todate=datetime.datetime(2021, 3, 26),
        timeframe=bt.TimeFrame.Minutes,
    )
    
    cerebro.adddata(brf_min_bar)
    #cerebro.resampledata(brf_min_bar, timeframe=bt.TimeFrame.Minutes, compression=15)    
    cerebro.resampledata(brf_min_bar, timeframe=bt.TimeFrame.Days)
    print("Starting Portfolio Value: {}".format(cerebro.broker.getvalue()))

    # 3. Add strategy
    cerebro.addstrategy(TestStrategy)
    # cerebro.optstrategy(TestStrategy, maperiod=range(10, 31))
    
    # 4. Run the strategy
    cerebro.run()
    # print('Final Portfolio Value: {}'.format(cerebro.broker.getvalue()))
    
    # 5. Plot the result
    cerebro.plot(style="candlestick", 
                 plotdist = 0.1,                        # 设置图形之间的间距
                 barup = '#98df8a', bardown='#ff9896',  # 设置蜡烛图上涨和下跌的颜色
                 volup = '#98df8a', voldown='#ff9896'   # 设置成交量在行情上涨和下跌情况下的颜色
                )