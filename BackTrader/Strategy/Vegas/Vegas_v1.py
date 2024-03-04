import backtrader as bt
import talib
import backtrader.analyzers as btanalyzers
import time
from datetime import datetime
import os
from pathlib import Path

import pandas as pd

#filename ="BTCUSDT_15m_2017-8-2023-8_Monthly"

#filename ="BTCUSDT_15m_2020-1-2023-8_Monthly"
#filename="BTCUSDT_1h_2020-1-2023-7_Monthly"
#filename="ETHUSDT_5m_2023-7-2023-8_Monthly"
#filename="ETHUSDT_15m_2020-1-2023-8_Monthly"
#filename="BTCUSDT_15m_2017-8-2023-8_Monthly"
filename ="ETHUSDT_5m_2020-1-2023-8_Monthly"
#filename ="BTCUSDT_5m_2017-8-2023-8_Monthly"
#filename ="ETHUSDT_5m_2023-4-2023-8_Monthly"  
symbol = "BTCUSDT"
strategy_name = "Vegas"

class VolumeOscillator(bt.Indicator):
    lines = ('osc',)

    params = (
        ('short_period', 1),  # 短线长度
        ('long_period', 14),  # 长线长度
    )

    def __init__(self):      
        self.addminperiod(self.params.long_period)  # 设置最小数据周期
        self.short = bt.indicators.EMA(self.data.volume, period=self.p.short_period)
        self.long = bt.indicators.EMA(self.data.volume, period=self.p.long_period)

    def next(self):
        if self.data.volume[0] == 0:
            print("No volume is provided by the data vendor.")
            self.lines.osc[0] = 0
        else:
            self.lines.osc[0] = 100 * (self.short[0] - self.long[0]) / self.long[0]


class MyStrategy(bt.Strategy):
    params = (('short_period', 1), ('long_period', 14) )


    def __init__(self):
        print("init ...")
        self.addminperiod(676)
        talib.set_compatibility(1)
        
        self.bt_ema12 = bt.talib.EMA(self.data, timeperiod=12)
        self.bt_ema144 = bt.talib.EMA(self.data, timeperiod=144)
        self.bt_ema169 = bt.talib.EMA(self.data, timeperiod=169)
        self.bt_ema576 = bt.talib.EMA(self.data, timeperiod=576)
        self.bt_ema676 = bt.talib.EMA(self.data, timeperiod=676)
        self.Osc = VolumeOscillator(self.data, short_period=self.p.short_period, long_period=self.p.long_period)
        
        
        # region CrossOver------------------------------------
        self.ema12_Over_ema144 = bt.indicators.CrossOver(self.bt_ema12, self.bt_ema144)
        self.ema12_Over_ema676 = bt.indicators.CrossOver(self.bt_ema12, self.bt_ema676)
        self.ema144_Over_ema676 = bt.indicators.CrossOver(self.bt_ema144, self.bt_ema676)        
        self.close_Over_ema144 = bt.indicators.CrossOver(self.data.close, self.bt_ema144)
        self.close_Over_ema676 = bt.indicators.CrossOver(self.data.close, self.bt_ema676)
        # endregion        
        
        # region CrossDown------------------------------------
        self.ema12_Down_ema144 = bt.indicators.CrossDown(self.bt_ema12, self.bt_ema144)
        self.ema12_Down_ema676 = bt.indicators.CrossDown(self.bt_ema12, self.bt_ema144)
        self.ema144_Down_ema676 = bt.indicators.CrossDown(self.bt_ema144, self.bt_ema676)                
        self.close_Down_ema144 = bt.indicators.CrossDown(self.data.close, self.bt_ema144)
        self.close_Down_ema676 = bt.indicators.CrossDown(self.data.close, self.bt_ema676)  
        # endregion        

        # region plotinfo------------------------------------
        self.ema12_Over_ema144.plotinfo.plot = False
        self.ema12_Over_ema676.plotinfo.plot = False
        self.ema144_Over_ema676.plotinfo.plot = False
        self.close_Over_ema144.plotinfo.plot = False
        self.close_Over_ema676.plotinfo.plot = False

        self.ema12_Down_ema144.plotinfo.plot = False
        self.ema12_Down_ema676.plotinfo.plot = False
        self.ema144_Down_ema676.plotinfo.plot = False
        self.close_Down_ema144.plotinfo.plot = False
        self.close_Down_ema676.plotinfo.plot = False
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
        # endregion
        
    def next(self):
        print("A new bar datetime :" + str(self.data.datetime.datetime())+" close :"+ str(self.data.close[0]))
        
        # region 參數宣告--------------------------------------------------------        
        long_signal = False
        short_signal = False
        # endregion

        if self.bt_ema12[-1] > self.bt_ema144[-1] and self.bt_ema144[-1] > self.bt_ema676[-1] :
            long_signal = True
            #print("long_signal")
        if self.bt_ema12[-1] < self.bt_ema144[-1] and self.bt_ema144[-1] < self.bt_ema676[-1] :
            short_signal = True            
     
        # region 開倉條件--------------------------------------------------------
        if not self.position :
            if long_signal and self.data.close[-1] > self.bt_ema144[-1] and self.data.low[-1] < self.bt_ema144[-1] :
                size = self.broker.get_cash()/self.data.open[0] *0.95
                self.order = self.buy(size=size,price=self.data.open[0])
                self.pricein = self.data.open[0]
                self.stop_loss = self.pricein * 1.05
                self.datein = bt.num2date(self.datas[0].datetime[0])
                self.stoploss_data.clear()
                self.stoploss_data.append([self.data.high[-1],self.data.low[-1]])   
                self.allsize = size             
                #print(f"做多開倉時間:{self.datein} 開倉價格:{self.pricein} size:{self.getposition().size}")
                
            if short_signal and self.data.close[-1] < self.bt_ema144[-1] and self.data.high[-1] > self.bt_ema144[-1] :
                size = self.broker.get_cash()/self.data.open[0] *0.95
                self.sell(size=size,price=self.data.open[0])
                self.pricein = self.data.open[0]
                self.stop_loss = self.pricein * 0.95
                self.datein = bt.num2date(self.datas[0].datetime[0])
                self.stoploss_data.clear()
                self.stoploss_data.append([self.data.high[-1],self.data.low[-1]])  
                self.allsize = size             
                #print(f"做空開倉時間:{self.datein} 開倉價格:{self.pricein} size:{self.getposition().size}")

        # endregion

        # region 平倉條件--------------------------------------------------------

        if self.position :     
            
            if len(self.stoploss_data) == 3 :       
                self.stoploss_data = self.stoploss_data[1:]
            self.stoploss_data.append([self.data.high[0],self.data.low[0]])
                   
            if self.getposition().size > 0 :  
                print (len(self.stoploss_data)) 
                if self.data.close[0] < self.bt_ema676[0]:  #小於676止損
                    self.log_out(size=self.getposition().size, reason="小於676止損")
                    self.order = self.sell(size=self.getposition().size, price=self.data.close[0])                
                elif len(self.stoploss_data) == 3:   
                    
                    if self.data.high[0] > max(sublist[0] for sublist in self.stoploss_data) : #新的高點高於前一個高點
                        # 移除最低價的止損，將止損上移
                        self.stoploss_data = [sublist for sublist in self.stoploss_data if sublist != min(self.stoploss_data, key=lambda sublist: sublist[1])]
                        self.stoploss_data.append([self.data.high[0],self.data.low[0]])
                        print(f"止損上移{self.stoploss_data} size:{self.getposition().size}")                      

                                             
                    min_value  = min(sublist[1] for sublist in self.stoploss_data)
                    print(f"min: {min_value }")
                    print(f"close : {self.data.close[0]}")
                    if self.data.close[0] < min_value: # 收盤價低於最低價的止損，平倉   
                        self.log_out(size=self.getposition().size, reason="收盤價低於最低價的止損平倉")
                        self.order = self.sell(size=self.getposition().size, price=self.data.close[0])         
                if self.getposition().size > 0  and self.data.close[0] > self.stop_loss :
                    self.log_out(size=self.getposition().size/2, reason="做多階段性止盈")
                    self.sell(size=self.getposition().size/2, price=self.data.close[0])                                                    
                    self.stop_loss = self.stop_loss * 1.05
                    
            if self.getposition().size < 0 :                               
                if self.data.close[0] > self.bt_ema676[0]:  #大於676止損
                    self.log_out(size=self.getposition().size, reason="大於676止損")
                    self.buy(size=self.getposition().size)                        
                elif len(self.stoploss_data) == 3 :      
                    if self.data.low[0] < min(sublist[1] for sublist in self.stoploss_data) : #新的低點低於前一個低點                    
                        # 移除最高價的止損，將止損下移
                        self.stoploss_data = [sublist for sublist in self.stoploss_data if sublist != max(self.stoploss_data, key=lambda sublist: sublist[0])]
                        self.stoploss_data.append([self.data.high[0],self.data.low[0]])           
                        print(f"止損下移{self.stoploss_data} size:{self.getposition().size}")                      
                    
                    
                    max_value  = max(sublist[0] for sublist in self.stoploss_data)
                              
                    if self.data.close[0] > max_value: # 收盤價高於最高價的止損，平倉   
                        self.log_out(size=self.getposition().size, reason="收盤價高於最高價的止損平倉")
                        self.buy(size=self.getposition().size)                        
                if self.getposition().size < 0 and self.data.close[0] < self.stop_loss : # 階段性止盈
                    self.log_out(size=self.getposition().size/2, reason="做空階段性止盈")
                    self.buy(size=self.getposition().size/2, price=self.data.close[0])                               
                    self.stop_loss = self.stop_loss * 0.95
        # endregion

    def log_out(self, size, reason):   
        if size > 0 :               
            self.priceout = self.data.close[0]
            self.dateout = bt.num2date(self.datas[0].datetime[0])
            income = (self.priceout - self.pricein) * size              #做多 = (平倉價格- 開倉價格) x 成交數量
            pcntchange = str(round((self.priceout - self.pricein) / self.pricein, 4) *100) + "%"  #(現價-上一個交易日收盤價）/上一個交易日收盤價*100%             
            self.content_list.append({  'Symbol': symbol,
                                        'Strategy': strategy_name,
                                        '開倉價格': self.pricein,
                                        '平倉價格': self.priceout,
                                        '原止損價格': min(sublist[1] for sublist in self.stoploss_data),
                                        '開倉放向': '多',
                                        '開倉時間': self.datein,
                                        '關倉時間': self.dateout,                                        
                                        '倉位總數量': self.allsize,
                                        '倉位總金額': self.pricein * self.allsize,
                                        '平倉數量': size,
                                        '剩餘倉位': self.getposition().size - size,
                                        '平倉原因': reason,
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
                                        '平倉價格': self.priceout,
                                        '原止損價格': max(sublist[0] for sublist in self.stoploss_data),
                                        '開倉放向': '空',
                                        '開倉時間': self.datein,
                                        '關倉時間': self.dateout, 
                                        '倉位總數量': self.allsize * (-1),                                                                                    
                                        '倉位總金額': self.pricein * size * (-1),    
                                        '平倉數量': size * (-1),   
                                        '剩餘倉位': self.getposition().size - size,
                                        '平倉原因': reason,                                                                                                                 
                                        '實際收益': income,
                                        '收益率': pcntchange,
                                        '帳戶總金額': self.broker.getvalue(),
                                    })            
                        
    def stop(self):
        if self.getposition().size < 0 :
            self.log_out(size=self.getposition().size, reason="回測結束")
            self.buy(size=self.getposition().size)            
        elif self.getposition().size > 0 :
            self.log_out(size=self.getposition().size, reason="回測結束")
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
    # cerebro.addsizer(bt.sizers.PercentSizer, percents = 95)
    
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
        timeframe=bt.TimeFrame.Minutes,
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