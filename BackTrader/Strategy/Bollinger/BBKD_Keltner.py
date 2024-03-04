import backtrader as bt
import talib
import backtrader.analyzers as btanalyzers
import time
from datetime import datetime
import os
from pathlib import Path

import pandas as pd

#filename="BTCUSDT_15m_2020-1-2023-8_Monthly"
filename="BTCUSDT_15m_2023-4-2023-10_Monthly"
#filename="BTCUSDT_1h_2020-1-2023-7_Monthly"
#filename="BTCUSDT_1h_2023-8-2023-10_Monthly"


symbol = filename[:7]
strategy_name = "Bollinger"

class BollingerBand(bt.Indicator):
    lines = ('high', 'mid', 'low')
    params = (('period', 20), ('devfactor', 2))

    def __init__(self):
        sma = bt.indicators.SMA(self.data, period=self.params.period)
        std = bt.indicators.StdDev(self.data, period=self.params.period)
        self.lines.mid = sma
        self.lines.high = sma + self.params.devfactor * std
        self.lines.low = sma - self.params.devfactor * std

class KeltnerChannels(bt.Indicator):
    lines = ('high', 'mid', 'low')
    
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
        self.lines.high = ema + self.params.devfactor * Krangema
        self.lines.mid = ema
        self.lines.low = ema - self.params.devfactor * Krangema


class KDJ(bt.Indicator):  
    lines = ( 'k', 'd', 'j')

    params = (
        ('period', 169),
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
        self.lines.k = bt.indicators.EMA(self.rsv, period=3, plot=False)
        # D值=K值的3周期加权平均值
        self.lines.d = bt.indicators.EMA(self.lines.k, period=3, plot=False)
        # J=3*K-2*D        
        self.lines.j = 3 * self.lines.k - 2 * self.lines.d


class MyStrategy(bt.Strategy):
    # params = (('bbwidth', 0.04), ('bb_period', 20), ('bb_devfactor', 2), 
    #           ('kt_period', 20), ('kt_devfactor', 3), ('bbw_period', 20), ('bbw_devfactor', 2))
    
    
    params = (('bb_period', 20), ('bb_devfactor', 2), ('kt_devfactor', 1.5), ('kdj_period', 25))

    def __init__(self):
        print("init ...")
        self.addminperiod(676)
        
        self.bt_ema144 = bt.talib.EMA(self.data, timeperiod=144)
        self.bt_ema676 = bt.talib.EMA(self.data, timeperiod=676)

        self.kt = KeltnerChannels(self.data, period=self.p.bb_period, devfactor=self.p.kt_devfactor) 
        self.bb = BollingerBand(self.data, period=self.p.bb_period, devfactor=self.p.bb_devfactor)
        self.kdj = KDJ(self.data, period=self.p.kdj_period, period_dfast=3, period_dslow=3)


        # region plotinfo------------------------------------
        self.bb.plotinfo.subplot = False
        self.kt.plotinfo.subplot = False       
        #self.bb_width.plotinfo.subplot = False             
  
        # endregion        

        # region 設定參數--------------------------------------------------------
        self.stop_loss = 0 # 設定5%的止損    
        self.timer = 0
        self.order = None
        self.pricein = None     # 開倉價格
        self.datein = None      # 開倉日期
        self.priceout = None    # 平倉價格(每个bar结束的收盘价)
        self.dateout = None     # 平倉日期(每个bar结束的日期)       
        self.allsize = None     # 倉位總數量
        self.content_list = []
        self.long_signal = False
        self.short_signal = False
        self.close_long_signal = False
        self.close_short_signal = False

        self.lowest_price = None
        self.highest_price = None
        self.stoploss_data = []
        self.ordercase = 0
        self.stop_loss = 0
        self.key_line_high = 0
        self.key_line_low = 0
        self.openreason = None
        self.closereason = None
        self.open_bb_high = 0
        self.open_bb_mid = 0
        self.open_bb_low= 0
        self.open_kt_high = 0
        self.open_kt_low = 0
        self.open_kdj = 0
        # endregion
        
    def next(self):
        if len(self.datas[0]) == self.data0.buflen():
            return
        print("A new bar datetime :" + str(self.data.datetime.datetime())+" close :"+ str(self.data.close[0]))

        # region 目前趨勢--------------------------------------------------------        

        # endregion


        # region 平倉條件--------------------------------------------------------

        if self.position :                            
            if self.getposition().size > 0 :
                if self.kdj.j[0] > 80 :
                    self.close_long_signal = True

                match self.ordercase :
                    case 1:            
                        
                        if self.data.close[0] < self.stop_loss :
                            self.closereason = "【Case1 做多止損】close小於stop_loss"
                            self.log_out(size=self.getposition().size)
                            self.sell(size=self.getposition().size, price=self.data.open[1])                                                          
                        elif self.close_long_signal and self.kdj.j[0] < 80:
                            self.closereason = "【Case1 做多止盈】kdj下穿80"
                            self.log_out(size=self.getposition().size)
                            self.sell(size=self.getposition().size, price=self.data.open[1])
     
            elif self.getposition().size < 0 :
                if self.kdj.j[0] < 20 :
                    self.close_short_signal = True                

                match self.ordercase :
                    case -1:        
                        if self.data.close[0] > self.stop_loss :
                            self.closereason = "【Case-1 做空止損】close大於stop_loss"
                            self.log_out(size=self.getposition().size)
                            self.buy(size=self.getposition().size, price=self.data.open[1])                                           
                        elif self.close_short_signal and self.kdj.j[0] > 20:
                            self.closereason = "【Case-1 做空止盈】kdj上穿20"
                            self.log_out(size=self.getposition().size)
                            self.buy(size=self.getposition().size, price=self.data.open[1])

         # endregion


        # region 開倉條件--------------------------------------------------------
        if not self.position :
            self.ordercase = 0
            self.key_line_high = 0
            self.key_line_low = 0       

            if self.kt.high[0] > self.bb.high[0] and self.bb.low[0] > self.kt.low[0]:  # Bollinger Bands在Keltner Channels内部（擠壓條件）
                if self.data.close[0] < self.bb.low[0] and self.kdj.j[0] < 20:
                    self.long_signal = True    
                    self.short_signal = False
                    self.close_long_signal = False
                    self.close_short_signal = False

                if self.data.close[0] > self.bb.high[0] and self.kdj.j[0] > 80:
                    self.short_signal = True
                    self.long_signal = False    
                    self.close_long_signal = False
                    self.close_short_signal = False                    

            if self.long_signal and self.kdj.lines.k[0] > 20 and self.kdj.lines.k[-1] < 20:
                if self.data.close[0] > self.data.open[0] :               
                    size = self.broker.get_cash()/self.data.open[1] *0.95
                    self.order = self.buy(size=size,price=self.data.open[1])
                    self.pricein = self.data.open[1]
                    self.datein = bt.num2date(self.datas[0].datetime[0])                
                    self.allsize = size   
                    self.ordercase = 1
                    self.openreason = "【Case1 做多開倉】Long_Singal AND kdj上穿20 AND K線收漲"
                    # TODO 找近期最低點
                    self.stop_loss = self.data.low[0]
                else:
                    self.long_signal = False

            elif self.short_signal and self.kdj.lines.k[0] < 80 and self.kdj.lines.k[-1] > 80:
                if self.data.close[0] < self.data.open[0] :               
                    size = self.broker.get_cash()/self.data.open[1] *0.95
                    self.order = self.sell(size=size,price=self.data.open[1])
                    self.pricein = self.data.open[1]
                    self.datein = bt.num2date(self.datas[0].datetime[0])                
                    self.allsize = size   
                    self.ordercase = -1
                    self.openreason = "【Case-1 做空開倉】Short_Singal AND KDJ下穿80 AND K線收跌"
                    self.stop_loss = self.data.high[0]
                    print(self.openreason)
                else :
                    self.short_signal = False

            #做多開倉: low小於bb_low AND close大於bb_low AND 上漲 AND K > 20
            
            #指標
            self.open_bb_high = self.bb.high[0]
            self.open_bb_mid = self.bb.mid[0]
            self.open_bb_low= self.bb.low[0]
            self.open_kt_high = self.kt.high[0]
            self.open_kt_low = self.kt.low[0]
            self.open_kdj = self.kdj.j[0]                                

            print('no position')    

        # endregion

    def log_out(self, size):   
        if size > 0 :               
            self.priceout = self.data.close[0]
            self.dateout = bt.num2date(self.datas[0].datetime[0])
            income = (self.priceout - self.pricein) * size              #做多 = (平倉價格- 開倉價格) x 成交數量
            pcntchange = str(round((self.priceout - self.pricein) / self.pricein, 4) *100) + "%"  #(現價-上一個交易日收盤價）/上一個交易日收盤價*100%             
            self.content_list.append({  'Symbol': symbol,
                                        'Strategy': strategy_name,
                                        '開倉放向': '多',
                                        '開倉時間': self.datein,
                                        '關倉時間': self.dateout,                                           
                                        'open_bb_high' : self.open_bb_high,
                                        'open_bb_mid'  : self.open_bb_mid ,
                                        'open_bb_low'  : self.open_bb_low ,
                                        'open_kt_high' : self.open_kt_high,
                                        'open_kt_low'  : self.open_kt_low ,
                                        'open_kdj' : self.open_kdj,
                                        'close_bb_high' : self.bb.high[0],
                                        'close_bb_mid'  : self.bb.mid[0] ,
                                        'close_bb_low'  : self.bb.low[0],
                                        'close_kt_high' : self.kt.high[0],
                                        'close_kt_low'  : self.kt.low[0],
                                        'close_kdj' :self.kdj.j[0],   
                                        '開倉價格': self.pricein,
                                        '平倉價格': self.priceout,
                                        '止損價格': self.stop_loss,
                                        #'止盈關鍵價格': self.key_line_low,                                                                             
                                        '倉位總數量': self.allsize,
                                        '倉位總金額': self.pricein * self.allsize,
                                        '平倉數量': size,
                                        '剩餘倉位': self.getposition().size - size,
                                        '開倉原因': self.openreason,                                        
                                        '平倉原因': self.closereason,
                                        '實際收益': income,
                                        '收益率': pcntchange,
                                        '帳戶總金額': self.broker.getvalue(),
                                    })
        if size < 0 :               
            self.priceout =self.data.close[0]
            self.dateout = bt.num2date(self.datas[0].datetime[0])
            income = (self.pricein - self.priceout) * size * (-1)                 # 做空= (開倉價格- 平倉價格) x 成交數量 X 開倉方向
            pcntchange = str(round((self.priceout - self.pricein) / self.pricein, 4) * (-1) *100)+"%" #(現價-上一個交易日收盤價）/上一個交易日收盤價*100%       
            self.content_list.append({  'Symbol': symbol,
                                        'Strategy': strategy_name,
                                        '開倉放向': '空',
                                        '開倉時間': self.datein,
                                        '關倉時間': self.dateout,                                         
                                        'open_bb_high' : self.open_bb_high,
                                        'open_bb_mid'  : self.open_bb_mid ,
                                        'open_bb_low'  : self.open_bb_low ,
                                        'open_kt_high' : self.open_kt_high,
                                        'open_kt_low'  : self.open_kt_low ,
                                        'open_kdj' : self.open_kdj,
                                        'close_bb_high' : self.bb.high[0],
                                        'close_bb_mid'  : self.bb.mid[0] ,
                                        'close_bb_low'  : self.bb.low[0],
                                        'close_kt_high' : self.kt.high[0],
                                        'close_kt_low'  : self.kt.low[0],
                                        'close_kdj' :self.kdj.j[0], 
                                        '開倉價格': self.pricein,
                                        '平倉價格': self.priceout,
                                        '止損價格': self.stop_loss,
                                        #'止盈關鍵價格': self.key_line_high,
                                        '倉位總數量': self.allsize * (-1),                                                                                    
                                        '倉位總金額': self.pricein * size * (-1),    
                                        '平倉數量': size * (-1),   
                                        '剩餘倉位': self.getposition().size - size,
                                        '開倉原因': self.openreason,                                        
                                        '平倉原因': self.closereason,                                                                                                                
                                        '實際收益': income,
                                        '收益率': pcntchange,
                                        '帳戶總金額': self.broker.getvalue()
                                    })            
                        
    def stop(self):
        if self.getposition().size < 0 :
            self.log_out(size=self.getposition().size)
            self.buy(size=self.getposition().size)            
        elif self.getposition().size > 0 :
            self.log_out(size=self.getposition().size)
            self.sell(size=self.getposition().size)
        df = pd.DataFrame(self.content_list)
        now = datetime.now().strftime("%Y%m%d_%H%M")
        print(now)
        df.to_csv("C:\Data\Git\Quantitative\BackTrader\Output\\" + filename + "_" + strategy_name+ "訂單紀錄_"+now+".csv",encoding='utf-8-sig')
        print("ending")
   

if __name__ == "__main__":

    # Create a Cerebro entity----------------------------------------------------------
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1000000)

    # Add Data Feed------------------------------------------------------------
    pathfile = "C:\Data\Git\Quantitative\BackTrader\Input\\" + filename + ".csv"
    df = pd.DataFrame(
        pd.read_csv(pathfile, delimiter=",", index_col="Datetime", parse_dates=True)
    )
    # 將日期時間字串轉換成datetime格式，手動指定格式包含毫秒
    df.index = pd.to_datetime(df.index, format="mixed" , utc=True)

    brf_min_bar = bt.feeds.PandasData(
        dataname=df,
        timeframe=bt.TimeFrame.Minutes,
    )

    cerebro.adddata(brf_min_bar)


    # Add strategy------------------------------------------------------------
    cerebro.addstrategy(MyStrategy)   
    # Analyzer-----------------------------------------------------
    # cerebro.addanalyzer(btanalyzers.SharpeRatio,_name='sharpe') 
    # cerebro.addanalyzer(btanalyzers.DrawDown,_name='drawdown') 
    # cerebro.addanalyzer(btanalyzers.Returns, _name='returns')

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name = 'SharpeRatio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DW')

    # Run the strategy-----------------------------------------------------
    print("Starting Portfolio Value: {}".format(cerebro.broker.getvalue()))


    results = cerebro.run()
    print("End Portfolio Value: {}".format(cerebro.broker.getvalue()))
    
    strat = results[0]
    print('SR:', strat.analyzers.SharpeRatio.get_analysis())
    print('DW:', strat.analyzers.DW.get_analysis())

    # Extract Analysis -----------------------------------------------------
    # ratio_list=[[
    #     x.analyzers.returns.get_analysis()['rtot'], 
    #     x.analyzers.returns.get_analysis()['rnorm100'], 
    #     x.analyzers.drawdown.get_analysis()['max']['drawdown'], 
    #     x.analyzers.sharpe.get_analysis()['sharperatio']] for x in results]
    
    # ratio_df = pd.DataFrame (ratio_list, columns=[ 'Total_return', 'APR', 'drawdown', 'sharperatio'])
    # print (ratio_df)

    # Plot -------------------------------------------------------------------
    cerebro.plot(style="candle")
    
    print("ending")