import os
import backtrader as bt
import backtrader.analyzers as btanalyzers
import datetime
import pandas as pd
from pathlib import Path
from UliPlot.XLSX import auto_adjust_xlsx_column_width

filename ="ETHUSDT_4h_2020-1-2023-7_Monthly"
symbol = "ETHUSDT"
strategy_name = "Bollinger"

class BollingerBandsYellow(bt.Indicator):
    lines = ('upper', 'middle', 'lower')
    params = (('period', 6), ('devfactor', 2))

    def __init__(self):
        sma = bt.indicators.SMA(self.data, period=self.params.period)
        std = bt.indicators.StdDev(self.data, period=self.params.period)
        self.lines.middle = sma
        self.lines.upper = sma + self.params.devfactor * std
        self.lines.lower = sma - self.params.devfactor * std

class BollingerBandsRed(bt.Indicator):
    lines = ('upper', 'middle', 'lower')
    params = (('period', 6), ('devfactor', 2.5))

    def __init__(self):
        sma = bt.indicators.SMA(self.data, period=self.params.period)
        std = bt.indicators.StdDev(self.data, period=self.params.period)
        self.lines.middle = sma
        self.lines.upper = sma + self.params.devfactor * std
        self.lines.lower = sma - self.params.devfactor * std

class BollingerBandsWidth(bt.Indicator):
    lines = ('bbw',)
    params = (('period', 6), ('devfactor', 2))

    def __init__(self):
        basis = bt.indicators.SMA(self.data, period=self.params.period)
        dev = self.params.devfactor * bt.indicators.StdDev(self.data, period=self.params.period)
        self.lines.bbw = (basis + dev - (basis - dev)) / basis

class MyStrategy(bt.Strategy):
    # BTCUSDT_4H
    # params = (('bbwidth', 0.01), ('bby_period', 25), ('bby_devfactor', 2.5), 
    #           ('bbr_period', 25), ('bbr_devfactor', 3.75), ('bbw_period', 25), ('bbw_devfactor', 2.5))
    # ETHUSDT_4H
    params = (('bbwidth', 0.04), ('bby_period', 6), ('bby_devfactor', 2), 
              ('bbr_period', 6), ('bbr_devfactor', 2.5), ('bbw_period', 6), ('bbw_devfactor', 2))

    def __init__(self):
        self.addminperiod(6)
        self.bb_yellow = BollingerBandsYellow(self.data, period=self.p.bby_period, devfactor=self.p.bby_devfactor)
        self.bb_red = BollingerBandsRed(self.data, period=self.p.bbr_period, devfactor=self.p.bbr_devfactor)
        self.bb_width = BollingerBandsWidth(self.data, period=self.p.bbw_period, devfactor=self.p.bbw_devfactor)    
                
        self.CloseOverYellowUpper = bt.indicators.CrossOver(self.data.close, self.bb_yellow.lines.upper)        
        self.HighCrossRedUpper = bt.indicators.CrossOver(self.data.high, self.bb_red.lines.upper)        
        self.LowDownYellowMiddle = bt.indicators.CrossDown(self.data.low, self.bb_red.lines.middle)
        self.CloseDownYellowLow = bt.indicators.CrossDown(self.data.close, self.bb_yellow.lines.lower)        
        self.LowDownRedLower = bt.indicators.CrossDown(self.data.low, self.bb_red.lines.lower)        
        self.HighOverYellowMiddle = bt.indicators.CrossOver(self.data.high, self.bb_red.lines.middle)        

        # region 設定參數--------------------------------------------------------
        self.stop_loss = 0 # 設定5%的止損    
        self.timer = 0
        self.order = None
        self.pricein = None     # 開倉價格
        self.datein = None      # 開倉日期
        self.priceout = None    # 平倉價格(每个bar结束的收盘价)
        self.dateout = None     # 平倉日期(每个bar结束的日期)       
        self.content_list = [] 
        # endregion
        #         
        # region plotinfo------------------------------------
        self.bb_yellow.plotinfo.subplot = False
        self.bb_red.plotinfo.subplot = False       
        self.CloseOverYellowUpper.plotinfo.plot = False
        self.HighCrossRedUpper.plotinfo.plot = False
        self.LowDownYellowMiddle.plotinfo.plot = False
        self.CloseDownYellowLow.plotinfo.plot = False
        self.LowDownRedLower.plotinfo.plot = False
        self.HighOverYellowMiddle.plotinfo.plot = False               
        # endregion       
        
    def next(self):
        self.timer += 1
        print(self.timer)
       
        # region 買入信號--------------------------------------------------------
        if not self.position:  # 如果沒有持倉，則可以考慮開倉
            if self.CloseOverYellowUpper[-1] == True and self.bb_width[-1] > self.p.bbwidth :  # 當前一根K線價格上穿bb_yellow的上軌時做多
                self.buy(price=self.data.open[0])
                self.stop_loss = self.data.open[0] * 0.95
                self.timer = 0
                self.pricein = self.data.open[0]
                self.datein = bt.num2date(self.data.datetime[0])     
                                
            elif self.CloseDownYellowLow[-1] == True and self.bb_width[-1] > self.p.bbwidth :   # 當前一根K線價格下穿bb_yellow的下軌時做空
                self.sell(price=self.data.open[0])
                self.stop_loss = self.data.open[0] * 1.05
                self.timer = 0
                self.pricein = self.data.open[0]
                self.datein = bt.num2date(self.data.datetime[0])                
        #endregion
        # region 移動止盈止損--------------------------------------------------------
        if self.position:                                               
            if self.getposition().size > 0 and self.timer > 0:  # 如果有多頭持倉
                if self.HighCrossRedUpper == True :  # 當K線價格有上穿bb_red的上軌時，移動止盈
                    self.log()  
                    self.sell()                    
                elif self.LowDownYellowMiddle == True : # 當K線價格有下穿bb_yellow的中軌時，移動止損
                    self.log()   
                    self.sell()
                # elif self.data.close[0] < self.stop_loss: # 如果有多頭持倉且價格低於止損價格
                #     a = self.data.close[0]

                #     self.log()  
                #     self.sell()            
            elif self.getposition().size < 0 and self.timer > 0: # 如果有空頭持倉            
                if self.LowDownRedLower == True :  # 當K線價格有下穿bb_red的下軌時，移動止盈
                    self.log()
                    self.buy()
                elif self.HighOverYellowMiddle == True :  # 當K線價格有上穿bb_yellow的中軌時，移動止損
                    self.log()       
                    self.buy()
                # elif self.data.close[0] > self.stop_loss: # 如果有空頭持倉且價格高於止損價格
                #     a = self.data.close[0]
                #     self.log()  
                #     self.buy()                       
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
        # fromdate=datetime.datetime(2021, 2, 28),
        # todate=datetime.datetime(2021, 3, 26),
        timeframe=bt.TimeFrame.Minutes,
    )

    cerebro.adddata(brf_min_bar)
    #cerebro.resampledata(brf_min_bar, timeframe=bt.TimeFrame.Minutes, compression=15)
    #cerebro.resampledata(brf_min_bar, timeframe=bt.TimeFrame.Days)


    # Add strategy------------------------------------------------------------
    cerebro.addstrategy(MyStrategy)
    # cerebro.optstrategy(TestStrategy, maperiod=range(10, 31))
    
    # Add writer------------------------------------------------------------
    # cerebro.addwriter(bt.WriterFile, csv=True, out= "C:\Data\Git\Quantitative\BackTrader\Output\\" + filename + "_" + strategy_name+ "_output.csv")
                      
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