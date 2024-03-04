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

class BollingerBandsYellow(bt.Indicator):
    lines = ('high', 'mid', 'low')
    params = (('period', 20), ('devfactor', 2))

    def __init__(self):
        sma = bt.indicators.SMA(self.data, period=self.params.period)
        std = bt.indicators.StdDev(self.data, period=self.params.period)
        self.lines.mid = sma
        self.lines.high = sma + self.params.devfactor * std
        self.lines.low = sma - self.params.devfactor * std

class BollingerBandsRed(bt.Indicator):
    lines = ('high', 'mid', 'low')
    params = (('period', 20), ('devfactor', 3))

    def __init__(self):
        sma = bt.indicators.SMA(self.data, period=self.params.period)
        std = bt.indicators.StdDev(self.data, period=self.params.period)
        self.lines.mid = sma
        self.lines.high = sma + self.params.devfactor * std
        self.lines.low = sma - self.params.devfactor * std

class BollingerBandsWidth(bt.Indicator):
    lines = ('bbw',)
    params = (('period', 20), ('devfactor', 2))

    def __init__(self):
        basis = bt.indicators.SMA(self.data, period=self.params.period)
        dev = self.params.devfactor * bt.indicators.StdDev(self.data, period=self.params.period)
        self.lines.bbw = (basis + dev - (basis - dev)) / basis

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
    params = (('bbwidth', 0.04), ('bby_period', 20), ('bby_devfactor', 2), 
              ('bbr_period', 20), ('bbr_devfactor', 3), ('bbw_period', 20), ('bbw_devfactor', 2))


    def __init__(self):
        print("init ...")
        self.addminperiod(676)
        
        self.bt_ema144 = bt.talib.EMA(self.data, timeperiod=144)
        self.bt_ema676 = bt.talib.EMA(self.data, timeperiod=676)

        self.bby = BollingerBandsYellow(self.data, period=self.p.bby_period, devfactor=self.p.bby_devfactor)
        self.bbr = BollingerBandsRed(self.data, period=self.p.bbr_period, devfactor=self.p.bbr_devfactor)
        self.bb_width = BollingerBandsWidth(self.data, period=self.p.bbw_period, devfactor=self.p.bbw_devfactor)     
        self.Kdj = KDJ(self.data, period=169, period_dfast=3, period_dslow=3)


        # region plotinfo------------------------------------
        self.bby.plotinfo.subplot = False
        self.bbr.plotinfo.subplot = False       
        self.bb_width.plotinfo.subplot = False             
  
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
        self.lowest_price = None
        self.highest_price = None
        self.stoploss_data = []
        self.ordercase = 0
        self.stop_loss = 0
        self.key_line_high = 0
        self.key_line_low = 0
        self.openreason = None
        self.closereason = None
        self.open_bby_high = 0
        self.open_bby_mid = 0
        self.open_bby_low= 0
        self.open_bbr_high = 0
        self.open_bbr_low = 0
        self.open_k = 0
        self.open_bbw = 0

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
                if self.ordercase == 1 :
                    print('ordercase : 1 ') 
                    # 止損
                    if self.data.close[0] < self.stop_loss :
                        self.closereason = "【Case1 做多止損】close小於stop_loss"
                        self.log_out(size=self.getposition().size)
                        self.sell(size=self.getposition().size, price=self.data.open[1])
                    # 止盈                   
                        
                    elif self.data.high[0] > self.bby.high[0] and self.data.close[0] < self.bbr.high[0] and self.Kdj.lines.k[0] < 80 :
                        self.closereason = "【Case1 做多階段性止盈】high大於bby_high close小於bbr_high AND k < 80"
                        self.log_out(size=self.getposition().size/2)
                        self.sell(size=self.getposition().size/2, price=self.data.open[1])


                    if self.data.close[0] > self.bby.mid[0] and self.data.high[0] < self.bby.high[0]:
                        self.ordercase = 2
                        self.stop_loss = self.data.low[0]

                    elif self.data.high[0] > self.bby.high[0] :
                        self.ordercase = 3
                        self.key_line_high = self.data.high[0]
                        self.key_line_low = self.data.low[0]               

                elif self.ordercase == 2 :
                    # 止損
                    if self.data.close[0] < self.stop_loss :
                        self.closereason = "【Case2 做多止損】close小於stop_loss"                  
                        self.log_out(size=self.getposition().size)
                        self.sell(size=self.getposition().size, price=self.data.open[1])                         
                    elif self.data.high[0] > self.bby.high[0] and self.data.close[0] < self.bbr.high[0] and self.Kdj.lines.k[0] < 80 :
                        self.closereason = "【Case1 做多止盈】high大於bby_high close小於bbr_high AND k < 80"
                        self.log_out(size=self.getposition().size)
                        self.sell(size=self.getposition().size, price=self.data.open[1])

                    if self.data.high[0] > self.bby.high[0] :
                        self.ordercase = 3
                        self.key_line_high = self.data.high[0]
                        self.key_line_low = self.data.low[0]                                

                    print('ordercase : 2 ')

                if self.ordercase == 3 :
                    print('ordercase : 3')
                    
                    if self.data.close[0] < self.key_line_low :
                        self.closereason = "【Case3 做多止盈】low 小於關鍵K線低點"                                  
                        self.log_out(size=self.getposition().size)
                        self.sell(size=self.getposition().size, price=self.data.open[1]) 
                        
                    elif self.data.close[0] > self.key_line_high and self.Kdj.lines.k[0] > 80 :
                        self.key_line_high = self.data.high[0]
                        self.key_line_low = self.data.low[0]                            
                    
            elif self.getposition().size < 0 :
                if self.ordercase == -1 :
                    print('ordercase : -1 ') 
                    # 止損
                    if self.data.close[0] > self.stop_loss :
                        self.closereason = "【Case-1 做空止損】close大於stop_loss"
                        self.log_out(size=self.getposition().size)
                        self.buy(size=self.getposition().size, price=self.data.open[1])      
                    # 止盈
                      
                    elif self.data.low[0] < self.bby.low[0] and self.data.close[0] > self.bbr.low[0] and self.Kdj.lines.k[0] > 20 :
                        self.closereason = "【Case-1 做空階段性止盈】low小於bby_low close大於bbr_low K > 20"
                        self.log_out(size=self.getposition().size/2)
                        self.buy(size=self.getposition().size/2, price=self.data.open[1])      

                    if self.data.close[0] < self.bby.mid[0] and self.data.low[0] > self.bby.low[0]:
                        self.ordercase = -2
                        self.stop_loss = self.data.high[0]

                    if self.data.low[0] < self.bby.low[0] :
                        self.ordercase = -3
                        self.key_line_high = self.data.high[0]
                        self.key_line_low = self.data.low[0]               


                elif self.ordercase == -2 :
                    # 止損
                    if self.data.close[0] > self.stop_loss :
                        self.closereason = "【Case-2 做空止損】close大於stop_loss"                  
                        self.log_out(size=self.getposition().size)
                        self.buy(size=self.getposition().size, price=self.data.open[1])  
                                               
                    elif self.data.low[0] < self.bby.low[0] and self.data.close[0] > self.bbr.low[0] and self.Kdj.lines.k[0] > 20 :
                        self.closereason = "【Case-2 做空階段性止盈】low小於bby_low close大於bbr_low K > 20"
                        self.log_out(size=self.getposition().size/2)
                        self.buy(size=self.getposition().size/2, price=self.data.open[1])      

                    if  self.data.low[0] < self.bby.low[0] :
                        self.ordercase = -3
                        self.key_line_high = self.data.high[0]
                        self.key_line_low = self.data.low[0]                                    

                    print('ordercase : 2 ')

                if self.ordercase == -3 :
                    print('ordercase : 3 ')
                    
                    if self.data.close[0] > self.key_line_high :
                        self.closereason = "【Case-3 做空止盈】high 大於關鍵K線高點"                                  
                        self.log_out(size=self.getposition().size)
                        self.buy(size=self.getposition().size, price=self.data.open[1]) 
                        
                    elif self.data.close[0] < self.key_line_low and self.Kdj.lines.k[0] < 20 :
                        self.key_line_high = self.data.high[0]
                        self.key_line_low = self.data.low[0]    

         # endregion


        # region 開倉條件--------------------------------------------------------
        if not self.position :
            self.ordercase = 0
            self.key_line_high = 0
            self.key_line_low = 0       
            #做多開倉: low小於bby_low AND close大於bby_low AND 上漲 AND K > 20
            
            if ( self.data.low[0] < self.bby.low[0] and self.data.close[0] > self.bby.low[0] and self.data.close[0] > self.data.open[0] and self.Kdj.lines.k[0] > 20 ) :               
                size = self.broker.get_cash()/self.data.open[1] *0.95
                self.order = self.buy(size=size,price=self.data.open[1])
                self.pricein = self.data.open[1]
                self.datein = bt.num2date(self.datas[0].datetime[0])                
                self.allsize = size   
                self.ordercase = 1
                self.openreason = "【Case1 做多開倉】low小於bby_low AND close大於bby_low AND K > 20 "
                self.stop_loss = self.data.low[0]

            # elif ( self.data.low[0] < self.bby.mid[0] and self.data.close[0] > self.bby.mid[0] and self.data.close[0] > self.data.open[0] and self.Kdj.lines.k[0] > 60 ) and self.bt_ema144[0] > self.bt_ema676[0]:               
            #     size = self.broker.get_cash()/self.data.open[1] *0.95
            #     self.order = self.buy(size=size ,price=self.data.open[1])
            #     self.pricein = self.data.open[1]
            #     self.datein = bt.num2date(self.datas[0].datetime[0])                
            #     self.allsize = size   
            #     self.ordercase = 2
            #     self.openreason = "【Case2 做多開倉】low小於bby_mid AND close大於bby_mid AND K > 60"
            #     self.stop_loss = self.data.low[0]
            #     print(self.openreason)                

            #做空開倉 high大於bby_high AND close小於bby_high AND 下跌 AND K < 80

            if ( self.data.high[0] > self.bby.high[0] and self.data.close[0] < self.bby.high[0] and self.data.close[0] < self.data.open[0] and self.Kdj.lines.k[0] < 80 ) :               
                size = self.broker.get_cash()/self.data.open[1] *0.95
                self.order = self.sell(size=size,price=self.data.open[1])
                self.pricein = self.data.open[1]
                self.datein = bt.num2date(self.datas[0].datetime[0])                
                self.allsize = size   
                self.ordercase = -1
                self.openreason = "【Case -1 做空開倉】high大於bby_high AND close小於bby_high AND K < 80 "
                self.stop_loss = self.data.high[0]
                print(self.openreason)
                
            # elif ( self.data.high[0] > self.bby.mid[0] and self.data.close[0] < self.bby.mid[0] and self.data.close[0] < self.data.open[0] and self.Kdj.lines.k[0] < 40 and self.bt_ema144[0] < self.bt_ema676[0]):              
            #     size = self.broker.get_cash()/self.data.open[1] *0.95
            #     self.order = self.sell(size=size ,price=self.data.open[1])
            #     self.pricein = self.data.open[1]
            #     self.datein = bt.num2date(self.datas[0].datetime[0])                
            #     self.allsize = size   
            #     self.ordercase = -2
            #     self.openreason = "【Case2 做空開倉】high大於bby_mid AND close小於bby_mid AND K < 40"
            #     self.stop_loss = self.data.high[0]                
            #     print(self.openreason)                      

            #指標
            self.open_bby_high = self.bby.high[0]
            self.open_bby_mid = self.bby.mid[0]
            self.open_bby_low= self.bby.low[0]
            self.open_bbw= self.bb_width[0]
            self.open_bbr_high = self.bbr.high[0]
            self.open_bbr_low = self.bbr.low[0]
            self.open_k = self.Kdj.lines.k[0]                                

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
                                        'open_bby_high' : self.open_bby_high,
                                        'open_bby_mid'  : self.open_bby_mid ,
                                        'open_bby_low'  : self.open_bby_low ,
                                        'open_bbr_high' : self.open_bbr_high,
                                        'open_bbr_low'  : self.open_bbr_low ,
                                        'open_bbw'      : self.open_bbw ,                                        
                                        'open_k' : self.open_k,
                                        'close_bby_high' : self.bby.high[0],
                                        'close_bby_mid'  : self.bby.mid[0] ,
                                        'close_bby_low'  : self.bby.low[0],
                                        'close_bbr_high' : self.bbr.high[0],
                                        'close_bbr_low'  : self.bbr.low[0],
                                        'close_bbw'      : self.bb_width[0] ,                                                                                    
                                        'close_k' :self.Kdj.lines.k[0],   
                                        '開倉價格': self.pricein,
                                        '平倉價格': self.priceout,
                                        '止損價格': self.stop_loss,
                                        '止盈關鍵價格': self.key_line_low,                                                                             
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
                                        'open_bby_high' : self.open_bby_high,
                                        'open_bby_mid'  : self.open_bby_mid ,
                                        'open_bby_low'  : self.open_bby_low ,
                                        'open_bbr_high' : self.open_bbr_high,
                                        'open_bbr_low'  : self.open_bbr_low ,
                                        'open_bbw'      : self.open_bbw ,
                                        'open_k' : self.open_k,
                                        'close_bby_high' : self.bby.high[0],
                                        'close_bby_mid'  : self.bby.mid[0] ,
                                        'close_bby_low'  : self.bby.low[0],
                                        'close_bbr_high' : self.bbr.high[0],
                                        'close_bbr_low'  : self.bbr.low[0],
                                        'close_bbw'      : self.bb_width[0] ,                                       
                                        'close_k' :self.Kdj.lines.k[0], 
                                        '開倉價格': self.pricein,
                                        '平倉價格': self.priceout,
                                        '止損價格': self.stop_loss,
                                        '止盈關鍵價格': self.key_line_high,
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