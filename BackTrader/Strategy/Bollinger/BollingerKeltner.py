import os
import backtrader as bt
import backtrader.analyzers as btanalyzers
import datetime
import pandas as pd
from pathlib import Path
import numpy as np

#filename ="BTCUSDT_1h_20230813"
#filename ="BTCUSDT_1h_2020-1-2023-7_Monthly"
#filename ="BTCUSDT_1h_2017-8-2023-8_Monthly"
filename ='BTCUSDT_15m_2023-4-2023-10_Monthly'
symbol = "BTCUSDT"
strategy_name = "BollingerKeltner"

class BollingerBands(bt.Indicator):
    lines = ('upper', 'middle', 'lower')
    params = (('period', 20), ('devfactor', 2))

    def __init__(self):
        sma = bt.indicators.SMA(self.data, period=self.params.period)
        std = bt.indicators.StdDev(self.data, period=self.params.period)
        self.lines.middle = sma
        self.lines.upper = sma + self.params.devfactor * std
        self.lines.lower = sma - self.params.devfactor * std
        #self.plotinfo.plotmaster = self.data

class KeltnerChannels(bt.Indicator):
    lines = ('upper', 'middle', 'lower')
    
    params = (
        ('period', 20),      # 均值移动周期
        ('devfactor', 1.5),  # 平均真实波幅乘数
    )
    def TrueRange(self):
        tr = bt.Max(self.data.high - self.data.low,
                    abs(self.data.high - self.data.close(-1)),
                    abs(self.data.low - self.data.close(-1)))
        return tr
    
    def __init__(self):
        ema = bt.indicators.EMA(self.data, period=self.params.period)
        Krange = self.TrueRange()
        Krangema = bt.indicators.EMA(Krange, period=self.params.period)
        self.lines.middle = ema
        self.lines.upper = ema + self.params.devfactor * Krangema
        self.lines.lower = ema - self.params.devfactor * Krangema

class KDJ(bt.Indicator):  
    lines = ( 'j',)

    params = (
        ('period', 25),
        ('period_dfast', 3),
        ('period_dslow', 3),
    )

    def __init__(self):
        self.high_nine = bt.indicators.Highest(self.data.high, period=self.p.period)
        self.low_nine = bt.indicators.Lowest(self.data.low, period=self.p.period)

        # 计算rsv值
        self.rsv = 100 * bt.DivByZero(
            self.data_close - self.low_nine, self.high_nine - self.low_nine, zero=None
        )
        
        # 计算rsv的3周期加权平均值，即K值
        k = bt.indicators.EMA(self.rsv, period=3, plot=False)
        # D值=K值的3周期加权平均值
        d = bt.indicators.EMA(k, period=3, plot=False)
        # J=3*K-2*D        
        self.lines.j = 3 * k - 2 * d
  
class MyStrategy(bt.Strategy):
    params = (('bb_period', 20), ('bb_devfactor', 2), ('kt_devfactor', 1.5))

    def __init__(self):
        # self.addminperiod(20)
        self.kt = KeltnerChannels(self.data, period=self.p.bb_period, devfactor=self.p.kt_devfactor)    
        self.bb = BollingerBands(self.data, period=self.p.bb_period, devfactor=self.p.bb_devfactor)    
        self.Kdj = KDJ(self.data, period=25, period_dfast=3, period_dslow=3)
        
        # region 設定參數--------------------------------------------------------
        self.stop_loss = 0 # 設定5%的止損    
        self.timer = 0
        self.order = None
        self.pricein = None     # 開倉價格
        self.datein = None      # 開倉日期
        self.priceout = None    # 平倉價格(每个bar结束的收盘价)
        self.dateout = None     # 平倉日期(每个bar结束的日期)       
        self.content_list = []
        self.long_signal = False
        self.short_signal = False
        self.lowest_price = None
        self.highest_price = None        
        # endregion

        # region plotinfo------------------------------------
        self.bb.plotinfo.subplot = False
        self.kt.plotinfo.subplot = False    
        # endregion       
        
    def next(self):
        bb_upper = self.bb.lines.upper[-1]
        bb_lower = self.bb.lines.lower[-1]
        keltner_upper = self.kt.lines.upper[-1]
        keltner_lower = self.kt.lines.lower[-1]    
        
        # region 買入信號-------------------------------------------------------- 
        if keltner_upper > bb_upper and bb_lower > keltner_lower:  # Bollinger Bands在Keltner Channels内部（擠壓條件）
            if self.data.close[-1] < bb_lower and self.Kdj.lines.j[-1] < 20:
                self.long_signal = True    
                self.short_signal = False
                print(f"long_signal 時間:{bt.num2date(self.data.datetime[-1])} 價格{self.data.close[-1]} J:{self.Kdj.lines.j[-1]}")
                print(f"keltner_upper : {keltner_upper} bb_upper : {bb_upper} bb_lower  : {bb_lower} keltner_lower: {keltner_lower}")
            if self.data.close[-1] > bb_upper and self.Kdj.lines.j[-1] > 80:
                self.short_signal = True
                self.long_signal = False    
                print(f"short_signal 時間:{bt.num2date(self.data.datetime[-1])} 價格{self.data.close[-1]} J:{self.Kdj.lines.j[-1]}")
                print(f"keltner_upper : {keltner_upper} bb_upper : {bb_upper} bb_lower  : {bb_lower} keltner_lower: {keltner_lower}")

        if self.long_signal:
            if self.lowest_price == None or self.lowest_price > self.data.low[-1]:
                self.lowest_price = self.data.low[-1]

        if self.short_signal:
            if self.highest_price == None or self.highest_price < self.data.high[-1]:
                self.highest_price = self.data.high[-1]                


    
        if self.long_signal and self.Kdj.lines.j[-1] >= 20 and self.Kdj.lines.j[-2] < 20 :            
            if not self.position and self.data.close[-1] > self.data.open[-1]:
                self.order = self.buy(price=self.data.open[0])
                self.stop_loss = self.lowest_price
                self.pricein = self.data.open[0]
                self.datein = bt.num2date(self.data.datetime[0])
                print(f"做多開倉時間:{self.datein} 開倉價格:{self.pricein}KDJ-2:{self.Kdj.lines.j[-2]}KDJ-1:{self.Kdj.lines.j[-1]}KDJ:{self.Kdj.lines.j[0]}")
            self.short_signal = False     
            self.lowest_price = None
            
        if self.short_signal and self.Kdj.lines.j[-1] <= 80 and self.Kdj.lines.j[-2] > 80 :
            if not self.position and self.data.close[-1] < self.data.open[-1]:
                self.order = self.sell(price=self.data.open[0])
                self.pricein = self.data.open[0]
                self.datein = bt.num2date(self.data.datetime[0])
                self.stop_loss = self.highest_price
                print(f"做空開倉時間:{self.datein} 開倉價格:{self.pricein}KDJ-2:{self.Kdj.lines.j[-2]}KDJ-1:{self.Kdj.lines.j[-1]}KDJ:{self.Kdj.lines.j[0]}")
            self.short_signal = False     
            self.highest_price = None       
        # endregion

        # region 移動止盈止損--------------------------------------------------------
        if self.position:                                               
            if self.getposition().size > 0 :  # 如果有多頭持倉
                if self.Kdj.lines.j[-1] >= 80 and self.Kdj.lines.j[0] < 80 or self.data.close[0] < self.stop_loss: 
                    print(f"做多止盈止損時間:{bt.num2date(self.data.datetime[0])} 止盈止損價格:{self.data.close[0]} stop_loss:{self.stop_loss}")
                    print(f"KDJ:{self.Kdj.lines.j[0]} close:{self.data.close[0]}")
                    self.log()  
                    self.sell()                            
            elif self.getposition().size < 0 : # 如果有空頭持倉   
                if self.Kdj.lines.j[-1] <= 20 and self.Kdj.lines.j[0] > 20 or self.data.close[0] > self.stop_loss:    
                    print(f"做空止盈止損時間:{bt.num2date(self.data.datetime[0])} 止盈止損價格:{self.data.close[0]} stop_loss:{self.stop_loss}")
                    print(f"KDJ:{self.Kdj.lines.j[0]} close:{self.data.close[0]}")                        
                    self.log()  
                    self.buy()                      
        #endregion                
                    

        
    def log(self):                  
        size = self.getposition().size
        if size > 0 :               
            self.priceout = self.data.close[0]
            self.dateout = bt.num2date(self.datas[0].datetime[0])
            income = (self.priceout - self.pricein) * size              #做多 = (平倉價格- 開倉價格) x 成交數量
            pcntchange = str(round((self.priceout - self.pricein) / self.pricein, 4) *100) + "%"  #(現價-上一個交易日收盤價）/上一個交易日收盤價*100%             
            self.content_list.append({  'Symbol': symbol,
                                        'Strategy': strategy_name,
                                        '開倉價格': self.pricein,
                                        '關倉價格': self.priceout,
                                        '開倉放向': '多',
                                        '開倉時間': self.datein,
                                        '關倉時間': self.dateout,                                        
                                        '成交數量': size,
                                        '倉位總金額': self.pricein * size,
                                        '實際收益': income,
                                        '收益率': pcntchange,
                                        '帳戶總金額': self.broker.getvalue(),
                                    })
        if size < 0 :               
            self.priceout = self.data.close[0]
            self.dateout = bt.num2date(self.datas[0].datetime[0])
            income = (self.pricein - self.priceout) * size * (-1)                 # 做空= (開倉價格- 平倉價格) x 成交數量 X 開倉方向
            pcntchange = str(round((self.priceout - self.pricein) / self.pricein, 4) * (-1) *100)+"%" #(現價-上一個交易日收盤價）/上一個交易日收盤價*100%       
            self.content_list.append({  'Symbol': symbol,
                                        'Strategy': strategy_name,
                                        '開倉價格': self.pricein,
                                        '關倉價格': self.priceout,
                                        '開倉放向': '空',
                                        '開倉時間': self.datein,
                                        '關倉時間': self.dateout,                                             
                                        '成交數量': size * (-1),   
                                        '倉位總金額': self.pricein * size * (-1),                                        
                                        '實際收益': income,
                                        '收益率': pcntchange,
                                        '帳戶總金額': self.broker.getvalue(),
                                    })
                        
    def stop(self):
        df = pd.DataFrame(self.content_list)
        df.to_csv("C:\Data\Git\Quantitative\BackTrader\Output\\" + filename + "_" + strategy_name+ "訂單紀錄.csv",encoding='utf-8-sig')
        print("ending")
        
if __name__ == "__main__":

    # Create a Cerebro entity----------------------------------------------------------
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1000000)
    cerebro.addsizer(bt.sizers.PercentSizer, percents = 95)
    
    # Add Data Feed------------------------------------------------------------
    pathfile = "C:\Data\Git\Quantitative\BackTrader\Input\\" + filename + ".csv"
    df = pd.DataFrame(
        pd.read_csv(pathfile, delimiter=",", index_col="Datetime", parse_dates=True)
    )
    # 將日期時間字串轉換成datetime格式，手動指定格式包含毫秒
    df.index = pd.to_datetime(df.index, format="mixed" , utc=True)

    brf_min_bar = bt.feeds.PandasData(
        dataname=df,
        # fromdate=datetime.datetime(2023, 5, 28),
        # todate=datetime.datetime(2023, 8, 5),
        # timeframe=bt.TimeFrame.Hours,
    )

    cerebro.adddata(brf_min_bar)
    #cerebro.resampledata(brf_min_bar, timeframe=bt.TimeFrame.Minutes, compression=60)
    #cerebro.resampledata(brf_min_bar, timeframe=bt.TimeFrame.Minutes, compression=15)
    #cerebro.resampledata(brf_min_bar, timeframe=bt.TimeFrame.Days)


    # Add strategy------------------------------------------------------------
    cerebro.addstrategy(MyStrategy)
    # cerebro.optstrategy(TestStrategy, maperiod=range(10, 31))
    
    # Add writer------------------------------------------------------------
    #cerebro.addwriter(bt.WriterFile, csv=True, out= "C:\Data\Git\Quantitative\BackTrader\Output\\" + filename + "_" + strategy_name+ "_output.csv")
                      
    # Analyzer-----------------------------------------------------
    cerebro.addanalyzer(btanalyzers.SharpeRatio,_name='sharpe') 
    cerebro.addanalyzer(btanalyzers.DrawDown,_name='drawdown') 
    cerebro.addanalyzer(btanalyzers.Returns, _name='returns')

    # Run the strategy-----------------------------------------------------
    print("Starting Portfolio Value: {}".format(cerebro.broker.getvalue()))
    results = cerebro.run()
    print("End Portfolio Value: {}".format(cerebro.broker.getvalue()))
        
    # Extract Analysis -----------------------------------------------------
    ratio_list=[[
        x.analyzers.returns.get_analysis()['rtot'], 
        x.analyzers.returns.get_analysis()['rnorm100'], 
        x.analyzers.drawdown.get_analysis()['max']['drawdown'], 
        x.analyzers.sharpe.get_analysis()['sharperatio']] for x in results]
    
    ratio_df = pd.DataFrame (ratio_list, columns=[ 'Total_return', 'APR', 'DrawDown', 'Sharpe_Ratio'])
    print (ratio_df)

    # Plot -------------------------------------------------------------------
    cerebro.plot(style="candle")
    
    print("ending")