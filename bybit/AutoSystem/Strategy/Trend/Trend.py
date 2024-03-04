import sys
sys.path.append("C:/Data/Git/Quantitative/bybit/AutoSystem/main")
from PerpBybit import PerpBybit
from Indicator import Indicator
from Common import Common
from DBHelper import DBHelper
import time
from datetime import datetime, timedelta
import json
import talib
import traceback
from multiprocessing import Process
from multiprocessing.dummy import Process

class Strategy(Process):
    
    def __init__(self):
        super(Strategy,self ).__init__()
        global run
        print("--- 開始執行時間：", datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "---")
      
        # region 讀取json設定值
        f = open("C:/Data/Git/Quantitative/bybit/AutoSystem/json/BoxScalper_Account.json")
        self.Account = json.load(f)
        f.close()
        
        f = open("C:/Data/Git/Quantitative/bybit/AutoSystem/json/Line.json")
        self.Line = json.load(f)
        f.close()        

        f = open("C:/Data/Git/Quantitative/bybit/AutoSystem/json/BoxScalper_Setting.json")
        self.Setting = json.load(f)
        f.close()
        #endregion

        # region 參數設定(之後由外部傳入)
        self.line_key = self.Line["LINE_API"]
        # self.symbol = self.Setting["symbol"]
        # self.pair = self.Setting["pair"]
        self.timeframe = self.Setting["Parameter"]["timeframe"]
        self.TSL_SL1 = self.Setting["Parameter"]["TSL_SL1"]
        self.TSL_SL2 = self.Setting["Parameter"]["TSL_SL2"]
        self.TP_Ts1 = self.Setting["Parameter"]["TP_Ts1"]
        self.TP_To = self.Setting["Parameter"]["TP_To"]                
        self.isLeverage = self.Setting["Parameter"]["isLeverage"]
        self.message = None
        self.account_name = None
        self.bybit_instances = {}
        # endregion

        # region Bybit API
        for account, account_data in self.Account.items():
            self.bybit_instances[account] = {
                "Bybit" : PerpBybit(
                    apiKey=account_data["apiKey"],
                    secret=account_data["secret"]
                ),
                "sendMessage" : account_data["sendMessage"],
                "amount" : account_data["amount"],
            }
        # endregion                     

    # region 買賣判斷
    def run(self):
        bybit_instances = self.bybit_instances
        first_account = next(iter(bybit_instances))
        bybit = bybit_instances[first_account]["Bybit"]
        first = True
        CloseOpeningHour = 24
        while True :
            now = datetime.now()
            if (now.minute == 0 and now.second == 1) or first: # 每小時重複一次 
                for symbol in self.Setting["Currency"]:
                    pair = symbol + "/USDT:USDT"
          


                try:
                    # region 計算指標數據 --------------------------------------------------------
                    
                    df = bybit.get_last_historical(self.symbol, self.timeframe, 1000)   # 獲取歷史K線數據 
                    df["ema_48"] = Indicator.ema(df["close"], timeperiod=48)
                    df["ema_226"] = Indicator.ema(df["close"], timeperiod=226)
                    
                    bby_high, bby_mid, bby_low = talib.BBANDS(df["close"],
                                                                                timeperiod=float(self.strategy[self.strategy_to_select]["parameter"]["bby_period"]),
                                                                                nbdevup=float(self.strategy[self.strategy_to_select]["parameter"]["bby_devfactor"]),
                                                                                nbdevdn=float(self.strategy[self.strategy_to_select]["parameter"]["bby_devfactor"]),
                                                                                matype=0)
                    
                    bbr_high, bbr_mid, bbr_low = talib.BBANDS(df["close"],
                                                                                timeperiod=float(self.strategy[self.strategy_to_select]["parameter"]["bbr_period"]),
                                                                                nbdevup=float(self.strategy[self.strategy_to_select]["parameter"]["bbr_devfactor"]),
                                                                                nbdevdn=float(self.strategy[self.strategy_to_select]["parameter"]["bbr_devfactor"]),
                                                                                matype=0)                    

                    df["bby_high"] = bby_high
                    df["bby_mid"] = bby_mid
                    df["bby_low"] = bby_low        
                    df["bbr_high"] = bbr_high
                    df["bbr_mid"] = bbr_mid
                    df["bbr_low"] = bbr_low                      
                    df['bbw'] = (df['bby_high'] - df['bby_low']) / df['bby_mid']
                    
                    volume_short = Indicator.ema(df["volume"], timeperiod=2)       
                    volume_long = Indicator.ema(df["volume"], timeperiod=28)       
                    df["volume_oscillator"] = 100 *(volume_short - volume_long)/volume_long

                    df['k'], df['d'] = talib.STOCH(df['high'].values,
                                                        df['low'].values, 
                                                        df['close'].values, 
                                                        fastk_period=float(self.strategy[self.strategy_to_select]["parameter"]["kdj_period"]), 
                                                        slowk_period=3, 
                                                        slowk_matype=0, 
                                                        slowd_period=3, 
                                                        slowd_matype=0)
                    
                    df['j'] = list(map(lambda x,y: 3*x-2*y, df['k'], df['d']))                                                                                       
                    #df.to_csv("C:\Data\Git\Quantitative\\bybit\AutoSystem\Output\作帳紀錄.csv",encoding='utf-8-sig')
                    
                    pre_row = df.iloc[-2]      
                    pre_two_row = df.iloc[-3]
                    
                    # region 目前趨勢 --------------------------------------------------------                                              
                    long_signal = False
                    short_signal = False                   
                    if pre_row.ema_48 > pre_row.ema_226 :
                        long_signal = True
                    if pre_row.ema_48 < pre_row.ema_226 :
                        short_signal = True                   
                    # endregion              
                                
                    dfnow = bybit.get_last_historical(self.symbol, '1m', 1) # 獲取當前價格
                    now_row = dfnow.iloc[-1]    

                            
                    print(  f"\n-----------------------------------------------------------------------------------------------\n"
                            f"\n現在時間:{now.strftime('%Y/%m/%d %H:%M:%S')} | "
                            f"【Strategy: {self.strategy_to_select}】 | "                               
                            f"【Symbol: {self.pair}】 | "                               
                            f"【TimeFrame: {self.timeframe}】 | "                               
                            f"【目前價格: {now_row.close}】\n"                                                                                                                                                    
                            f"【open:{pre_row.open}】 | "
                            f"【high:{pre_row.high}】 | "
                            f"【low:{pre_row.low}】 | "                                                                                                
                            f"【close:{pre_row.close}】\n"
                            f"【bby_high:{round(pre_row.bby_high, 2)}】 | "                                                                                                
                            f"【bby_mid:{round(pre_row.bby_mid, 2)}】 | "                                                                                             
                            f"【bby_low:{round(pre_row.bby_low, 2)}】 | "                                                                                             
                            f"【bbr_high:{round(pre_row.bbr_high, 2)}】 | "                                                                                                                         
                            f"【bbr_low:{round(pre_row.bby_low, 2)}】 | "                                                                                             
                            f"【bbw:{round(pre_row.bbw, 4)}】\n"                                                                                           
                            
                            
                            f"【ema_48:{round(pre_row.ema_48, 2)}】 | "
                            f"【ema_226:{round(pre_row.ema_226, 2)}】 | "                
                            f"【volume_oscillator:{round(pre_row.volume_oscillator, 2)}】 | "             
                            f"【k:{round(pre_row.k, 2)}】 | "            
                            f"【d:{round(pre_row.d ,2)}】 | "            
                            f"【j:{round(pre_row.j, 2)}】"                                                                                              
                        )                       
                                                                                                              
                    # endregion

                    for account, instance in bybit_instances.items():    
                        # region 主帳號交易                    
                        try: 
                            bybit = bybit_instances[account]["Bybit"]
                            self.account_name = account
                            self.stop_profit = None if bybit_instances[account]['StopProfit'] == None else float(bybit_instances[account]['StopProfit'])
                            self.stop_profit_percent = float(bybit_instances[account]['profit_percent'])    
                            self.profit_size_percent = float(bybit_instances[account]['profit_size_percent'])  
                            self.stop_loss_percent = float(bybit_instances[account]['loss_percent'])                                              
                            self.isLeverage = int(bybit_instances[account]['isLeverage'])
                            # 獲取 USD 餘額
                            usd_balance = float(bybit.get_wallet_balance("USDT"))
                            if bybit_instances[account]["sendMessage"] :
                                print(  f"\n【帳號: {self.account_name}】 | "       
                                        f"【USD 餘額: {round(usd_balance, 2)}】 | "     
                                        f"【止盈趴數: {self.stop_profit_percent}】 | "                                                                                                                                                                                                                           
                                        f"【止盈倉位趴數: {self.profit_size_percent}】 | "                                           
                                        f"【止損趴數: {self.stop_loss_percent}】 | "                                   
                                        f"【槓桿倍數: {self.isLeverage}】 | "        
                                    )                                   

                            # 獲取持倉信息     
                            position= bybit.get_position(self.pair) 
                            # region 判斷是否進行交易

                            # region 有持倉                           
                            if position["side"] != ""  :
                                orderhistory = bybit.get_order_history_byside(self.pair, position["side"], '')
                                oriOrderCase = bybit_instances[account]['OrderCase']                                                                                
                                
                                if orderhistory != None:
                                    CreatedTime = datetime.fromtimestamp(float(orderhistory['createdTime'])/1000).strftime("%Y/%m/%d %H:%M")
                                    UpdatedTime = datetime.fromtimestamp(float(orderhistory['updatedTime'])/1000).strftime("%Y/%m/%d %H:%M")
                                    OpeningHour = round((datetime.now() - datetime.fromtimestamp((float(orderhistory["createdTime"]))/1000)).total_seconds() / 3600, 2)
                                else :
                                    CreatedTime = '單量過多'
                                    UpdatedTime = '單量過多'
                                    OpeningHour = '單量過多'

                                if bybit_instances[account]["sendMessage"] :
                                    print(  f"目前持倉："
                                            f"【Side:{position['side']}】 | "  
                                            f"【AvgPrice:{position['avgPrice']}】 | "                                                                                      
                                            f"【Size:{position['size']}】 | "  
                                            f"【PositionValue:{position['positionValue']}】 | "                                                                                      
                                            f"【目前止盈價格: {self.stop_profit}】\n"      
                                            f"【key_line_high: { bybit_instances[account]['key_line_high']}】 | "  
                                            f"【key_line_low: { bybit_instances[account]['key_line_low']}】 | "                                                                                
                                            f"【CreatedTime: {CreatedTime}】 | "                                                                           
                                            f"【UpdatedTime: {UpdatedTime}】 | "  
                                            f"【OpeningHour: {OpeningHour}】 | "                                                                                                                                                                                                             
                                            f"【OrderCase: {bybit_instances[account]['OrderCase']}】"                                       
                                        )                                                    
                                if position["side"] == "Buy":
                                    # 初始化參數
                                    if bybit_instances[account]['OrderCase'] == 0 :
                                        bybit_instances[account]['key_line_high'] = float(pre_two_row.high)
                                        bybit_instances[account]['key_line_low'] = float(pre_two_row.low)                                           
                                        if pre_two_row.close < pre_two_row.bby_mid :
                                            bybit_instances[account]['OrderCase'] = 1
                                        elif pre_two_row.close > pre_two_row.bby_mid and pre_two_row.high < pre_two_row.bby_high:
                                            bybit_instances[account]['OrderCase'] = 2
                                        elif pre_two_row.high > pre_two_row.bby_high :
                                            bybit_instances[account]['OrderCase'] = 3    
                                                                                                                            
                                    if bybit_instances[account]['StopProfit'] != None :    
                                        if pre_row.high >= bybit_instances[account]['StopProfit'] :
                                            if bybit_instances[account]["sendMessage"] :
                                                message = (
                                                    f'\n帳號:{account}'
                                                    f'\n時間:{datetime.now().strftime("%Y/%m/%d %H:%M:%S")}'                                            
                                                    f"\n價格: {str(pre_row.high)}達做多階段性止盈目標位:{str(bybit_instances[account]['StopProfit'])}"
                                                )
                                                print(message)
                                                bybit.send_line_message(self.line_key, message) 

                                    match bybit_instances[account]['OrderCase']:
                                        case 1: # 正向做多模式    
                                            if pre_row.close < bybit_instances[account]['key_line_low'] :
                                                Common.close_order(self, bybit, "Sell", float(now_row.close), 1, bybit_instances[account]["sendMessage"],
                                                                f"【Case1 做多止損】close小於key_line_low{round(bybit_instances[account]['key_line_low'], 2)}")
                                            elif pre_row.high > pre_row.bby_high and pre_row.close < pre_row.bbr_high and pre_row.j < 80:
                                                Common.close_order(self, bybit, "Sell", float(now_row.close), 0.5, bybit_instances[account]["sendMessage"],
                                                                '【Case1 做多階段性止盈】high大於bby_high close小於bbr_high AND kdj < 80')        
                                                
                                            if pre_row.close > pre_row.bby_mid and pre_row.high < pre_row.bby_high :
                                                bybit_instances[account]['OrderCase'] = 2
                                                bybit_instances[account]['key_line_low'] = pre_row.low
                                                Common.reset_stop_loss(self, bybit, 'Sell', pre_row.low)                                                  
                                                
                                            elif pre_row.high > pre_row.bby_high :
                                                bybit_instances[account]['OrderCase'] = 3
                                                bybit_instances[account]['key_line_high'] = pre_row.high
                                                bybit_instances[account]['key_line_low'] = pre_row.low                                                                                                                                                                               
                                                Common.reset_stop_loss(self, bybit, 'Sell', pre_row.bby_mid)                                                                                              
                                            
                                        case 2: # 中線做多
                                            if pre_row.close < pre_row.bby_mid :
                                                Common.close_order(self, bybit, "Sell", float(now_row.close), 1, bybit_instances[account]["sendMessage"],
                                                                f'【Case2 做多止損】close小於bby_mid:{round(pre_row.bby_mid, 2)}')
                                            elif pre_row.high > pre_row.bby_high and pre_row.close < pre_row.bbr_high and pre_row.j < 80:
                                                Common.close_order(self, bybit, "Sell", float(now_row.close), 0.5, bybit_instances[account]["sendMessage"],
                                                                '【Case2 做多階段性止盈】high大於bby_high close小於bbr_high AND kdj < 80')        
                                                
                                            if  pre_row.high > pre_row.bby_high :
                                                bybit_instances[account]['OrderCase'] = 3
                                                bybit_instances[account]['key_line_high'] = pre_row.high
                                                bybit_instances[account]['key_line_low'] = pre_row.low                                                                                                                                                                               
                                                Common.reset_stop_loss(self, bybit, 'Sell', pre_row.low)      

                                        case 3:
                                            if pre_row.close < bybit_instances[account]['key_line_low'] :
                                                Common.close_order(self, bybit, "Sell", float(now_row.close), 1, bybit_instances[account]["sendMessage"],
                                                                f"【Case3 做多平倉】close小於key_line_low:{round(bybit_instances[account]['key_line_low'], 2)}") 
                                            elif pre_row.close > bybit_instances[account]['key_line_high'] and pre_row.j > 80 :
                                                bybit_instances[account]['key_line_high'] = pre_row.high
                                                bybit_instances[account]['key_line_low'] = pre_row.low
                                    # 重設止盈
                                    bybit_instances[account]['StopProfit'] = self.stop_profit = float(pre_row.bbr_high) * (1 + self.stop_profit_percent)
                                    Common.reset_stop_profit(self, bybit, 'Sell') #重設止盈需相反                                                                                       
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                                elif position["side"] == "Sell":
                                    
                                    # 初始化參數
                                    if bybit_instances[account]['OrderCase'] == 0 :
                                        bybit_instances[account]['key_line_high'] = float(pre_two_row.high)
                                        bybit_instances[account]['key_line_low'] = float(pre_two_row.low)                                        
                                        if pre_two_row.close > pre_two_row.bby_mid :
                                            bybit_instances[account]['OrderCase'] = -1
                                        elif pre_two_row.close < pre_two_row.bby_mid and pre_two_row.low > pre_two_row.bby_low:
                                            bybit_instances[account]['OrderCase'] = -2
                                        elif pre_two_row.low < pre_two_row.bby_low :
                                            bybit_instances[account]['OrderCase'] = -3       

                                        
                                    if bybit_instances[account]['StopProfit'] != None:    
                                        if pre_row.low <= bybit_instances[account]['StopProfit'] :
                                            if bybit_instances[account]["sendMessage"] :
                                                message = (
                                                    f'\n帳號:{account}'
                                                    f'\n時間:{datetime.now().strftime("%Y/%m/%d %H:%M:%S")}'                                            
                                                    f"\n價格: {str(pre_row.high)}達做空階段性止盈目標位:{str(bybit_instances[account]['StopProfit'])}"
                                                )
                                                print(message)
                                                bybit.send_line_message(self.line_key, message) 
                                                
                                    match bybit_instances[account]['OrderCase']:
                                        case -1: # 正向做空模式    
                                            if pre_row.close > bybit_instances[account]['key_line_high'] :
                                                Common.close_order(self, bybit, "Buy", float(now_row.close), 1, bybit_instances[account]["sendMessage"],
                                                                f"【Case-1 做空止損】close大於key_line_high:{round(bybit_instances[account]['key_line_high'], 2)}")
                                            elif pre_row.low < pre_row.bby_low and pre_row.close > pre_row.bbr_low and pre_row.j > 20:
                                                Common.close_order(self, bybit, "Buy", float(now_row.close), 0.5, bybit_instances[account]["sendMessage"],
                                                                '【Case-1 做空階段性止盈】low小於bby_low close大於bbr_low kdj > 20')        
                                                
                                            if pre_row.close < pre_row.bby_mid and pre_row.low > pre_row.bby_low :
                                                bybit_instances[account]['OrderCase'] = -2
                                                bybit_instances[account]['key_line_high'] = pre_row.high
                                                Common.reset_stop_loss(self, bybit, 'Buy', pre_row.high)                                                                                           
                                                                                                                                                                                            
                                            elif pre_row.low < pre_row.bby_low :
                                                bybit_instances[account]['OrderCase'] = -3
                                                bybit_instances[account]['key_line_high'] = pre_row.high
                                                bybit_instances[account]['key_line_low'] = pre_row.low                                                                                                                                                                               
                                                Common.reset_stop_loss(self, bybit, 'Buy', pre_row.bby_mid)                                                                                              
                                            
                                        case -2: # 中線做空
                                            if pre_row.close > pre_row.bby_mid :
                                                Common.close_order(self, bybit, "Buy", float(now_row.close), 1, bybit_instances[account]["sendMessage"],
                                                                f'【Case-2 做空止損】close大於bby_mid:{round(pre_row.bby_mid, 2)}')
                                            elif pre_row.low < pre_row.bby_low and pre_row.close > pre_row.bbr_low and pre_row.j > 20:
                                                Common.close_order(self, bybit, "Buy", float(now_row.close), 0.5, bybit_instances[account]["sendMessage"],
                                                                '【Case-2 做空階段性止盈】low小於bby_low close大於bbr_low kdj > 20')        
                                                
                                            if  pre_row.low < pre_row.bby_low :
                                                bybit_instances[account]['OrderCase'] = -3
                                                bybit_instances[account]['key_line_high'] = pre_row.high
                                                bybit_instances[account]['key_line_low'] = pre_row.low                                                                                                                                                                               
                                                Common.reset_stop_loss(self, bybit, 'Buy', pre_row.low)      

                                        case -3:
                                            if pre_row.close > bybit_instances[account]['key_line_high'] :
                                                Common.close_order(self, bybit, "Buy", float(now_row.close), 1, bybit_instances[account]["sendMessage"],
                                                                f"【Case-3 做空平倉】close大於key_line_high:{round(bybit_instances[account]['key_line_high'], 2)}")      
                                            elif pre_row.close < bybit_instances[account]['key_line_low'] and pre_row.j < 20 :
                                                bybit_instances[account]['key_line_high'] = pre_row.high
                                                bybit_instances[account]['key_line_low'] = pre_row.low
                                    # 重設止盈
                                    bybit_instances[account]['StopProfit'] = self.stop_profit = float(pre_row.bbr_low) * (1 - self.stop_profit_percent)
                                    Common.reset_stop_profit(self, bybit, 'Buy') #重設止盈需相反                                                   

                                if oriOrderCase != bybit_instances[account]['OrderCase'] :
                                    message = (
                                        f"\nOrderCase轉換為:{bybit_instances[account]['OrderCase']}"  
                                        f"\nkey_line_high: {str(bybit_instances[account]['key_line_high'])}"
                                        f"\nkey_line_low: {str(bybit_instances[account]['key_line_low'])}"
                                    )
                                    print(message)
                                    bybit.send_line_message(self.line_key, message)   
                            # endregion

                            # region 無持倉
                            position= bybit.get_position(self.pair) # 獲取持倉信息與可用餘額(有可能反向開倉)                        
                            usd_balance = float(bybit.get_wallet_balance("USDT"))
                            if position["side"] == "" :
                                print("無持倉")
                                bybit_instances[account]['OrderCase'] = 0       
                                bybit_instances[account]['StopProfit'] = None                 
                                bybit_instances[account]['key_line_high'] = None
                                bybit_instances[account]['key_line_low'] = None

                                # Case: 2 中線做多開倉
                                if (pre_row.low < pre_row.bby_mid and pre_row.close > pre_row.bby_mid and pre_row.close > pre_row.open and pre_row.j > 60 and long_signal) :
                                    self.ordercase = bybit_instances[account]['OrderCase'] = 2
                                    bybit_instances[account]['key_line_low'] = pre_row.low
                                    Common.open_order(self, bybit, 'Buy', float(now_row.close), bybit_instances[account]["sendMessage"], '【Case2】收盤價上穿bby_mid AND long_signal AND kdj > 60')
                                    Common.set_stop_loss(self, bybit, pre_row.bby_low)  

                                # Case: 1 正常做多開倉
                                elif (pre_row.low < pre_row.bby_low and pre_row.close > pre_row.bby_low and pre_row.close > pre_row.open and pre_row.j > 20) :
                                    self.ordercase = bybit_instances[account]['OrderCase'] = 1
                                    bybit_instances[account]['key_line_low'] = pre_row.low
                                    Common.open_order(self, bybit, 'Buy', float(now_row.close), bybit_instances[account]["sendMessage"], '【Case1】收盤價上穿bby_low AND kdj > 20')
                                    Common.set_stop_loss(self, bybit, pre_row.bbr_low)                                      
                                                                                                                        
                                # Case:-2 中線做空開倉
                                if (pre_row.high > pre_row.bby_mid and pre_row.close < pre_row.bby_mid and pre_row.close < pre_row.open and pre_row.j < 40 and short_signal) :
                                    self.ordercase = bybit_instances[account]['OrderCase'] = -2
                                    bybit_instances[account]['key_line_high'] = pre_row.high     
                                    Common.open_order(self, bybit, "Sell", float(now_row.close), bybit_instances[account]["sendMessage"], '【Case2】收盤價下穿bby_mid AND short_signal AND kdj < 40')
                                    Common.set_stop_loss(self, bybit, pre_row.bby_high)                                      

                                # Case:-1 正常做空開倉
                                elif (pre_row.high > pre_row.bby_high and pre_row.close < pre_row.bby_high and pre_row.close < pre_row.open and pre_row.j < 80) :
                                    self.ordercase = bybit_instances[account]['OrderCase'] = -1
                                    bybit_instances[account]['key_line_high'] = pre_row.high                                    
                                    Common.open_order(self, bybit, "Sell", float(now_row.close), bybit_instances[account]["sendMessage"], '【Case-1】收盤價下穿bby_high AND kdj < 80')
                                    Common.set_stop_loss(self, bybit, pre_row.bbr_high)                                      

                                    
                                # 設置倉位部分止盈
                                if bybit_instances[account]['OrderCase'] > 0 :
                                    bybit_instances[account]['StopProfit'] = self.stop_profit = float(pre_row.bbr_high) * (1 + self.stop_profit_percent)
                                    Common.set_stop_profit(self, bybit)
                                    
                                elif bybit_instances[account]['OrderCase'] < 0 :
                                    bybit_instances[account]['StopProfit'] = self.stop_profit = float(pre_row.bbr_low) * (1 - self.stop_profit_percent)
                                    Common.set_stop_profit(self, bybit)                                
                            # endregion   
                            
                            # endregion            
                        except BaseException as err:                                        
                            errmsg = (  f"【異常】\n{self.strategy_to_select}策略發生錯誤\n"
                                        f"錯誤訊息:{err}\n"                                            
                                        f"訂單資訊{self.message}\n"
                                        f"traceback{traceback.format_exc()}"                    
                                    )                        
                            bybit.send_line_message(self.line_key, errmsg)
                            print(errmsg)
                        # endregion



                    first = False                   
                    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=1)  # 計算下一個整點時間                    
                    time.sleep((next_hour - now - 10).total_seconds()) # 等待直到下一個整點 並扣除10秒保留

                except BaseException as err:                                        
                    errmsg = (  f"【異常】\n{self.strategy_to_select}策略發生錯誤\n"
                                f"錯誤訊息:{err}\n"                                            
                                f"訂單資訊{self.message}\n"
                                f"traceback{traceback.format_exc()}"                    
                            )                        
                    bybit.send_line_message(self.line_key, errmsg)
                    print(errmsg)
    # endregion

if __name__ == '__main__':
    BoxScalper = Strategy()
    BoxScalper.start()