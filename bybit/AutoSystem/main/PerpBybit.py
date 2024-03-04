import ccxt
import json
import requests
import pandas as pd

class PerpBybit():
    def __init__(self, test, apiKey=None, secret=None):
        bybit_auth_object = {
            'apiKey'            : apiKey,
            'secret'            : secret,
            'timeout'           : 15000,
            'enableRateLimit'   : True     
        }
        if bybit_auth_object['secret'] == None:
            self._auth = False
            self._session = ccxt.bybit()
        else:
            self._auth = True
            self._session = ccxt.bybit(bybit_auth_object)
            self._session.set_sandbox_mode(test)
        self.market = self._session.load_markets()       

# region 其他

    def authentication_required(fn):
        def wrapped(self, *args, **kwargs):
            if not self._auth:
                raise Exception('You must be authenticated to use this method')
            else:
                return fn(self, *args, **kwargs)
        return wrapped

    def convert_amount_to_precision(self, symbol, amount):
        try:        
            return self._session.amount_to_precision(symbol, amount)
        except:
            return 0     
            
    def convert_price_to_precision(self, symbol, price):
        return self._session.price_to_precision(symbol, price)

    # 發送Line訊息        
    def send_line_message(self, key, message) :       
        # HTTP 標頭參數與資料
        headers = { "Authorization": "Bearer " + key }
        data = { 'message': message }
        # 以 requests 發送 POST 請求
        try :
            requests.post("https://notify-api.line.me/api/notify",
                headers = headers, data = data)
            pass
        except BaseException as err:
            print(err)  
# endregion 其他            

# region 公有行情

    # region 取得歷史數據
    def get_last_historical(self, symbol, timeframe, limit):
        try:
            result = pd.DataFrame(self._session.fetch_ohlcv(symbol, timeframe, None, limit=limit))
            result = result.rename(
                columns={
                    0: 'timestamp',
                    1: 'open',
                    2: 'high',
                    3: 'low',
                    4: 'close',
                    5: 'volume'
                })
            result = result.set_index(result['timestamp'])
            result.index = pd.to_datetime(result.index, unit='ms')
            del result['timestamp']
            return result
        except BaseException as err:            
            raise Exception(f"An error occurred in function {__name__}: {err}") 
    # endregion

    # region OrderBook(深度)
    def get_orderbook(self, category, symbol, limit):
        try:
            request = {
                'category' : category,
                'symbol'   : symbol,
                'limit'    : limit   # spot: [1, 200], 默認: 1 | linear&inverse: [1, 200],默認: 25 | option: [1, 25],默認: 1
            }
            return self._session.publicGetV5MarketOrderbook(request)
        except BaseException as err:            
            raise Exception(f"An error occurred in function {__name__}: {err}") 
    # endregion

    # region 查詢最新行情信息
    def get_market_tickers(self, category, baseCoin, expDate):
        try:
            request = {
                'category' : category,
                'baseCoin' : baseCoin,      # baseCoin和symbol必傳其中一個
                'expDate'  : expDate        # 到期日 ex: 25DEC22
            }
            return self._session.publicGetV5MarketTickers(request)
            return result
        except BaseException as err:            
            raise Exception(f"An error occurred in function {__name__}: {err}") 
 
    #  Response ex
    # "symbol": "BTC-30DEC22-18000-C",
    # "bid1Price": "0",
    # "bid1Size": "0",
    # "bid1Iv": "0",
    # "ask1Price": "435",
    # "ask1Size": "0.66",
    # "ask1Iv": "5",
    # "lastPrice": "435",
    # "highPrice24h": "435",
    # "lowPrice24h": "165",
    # "markPrice": "0.00000009",
    # "indexPrice": "16600.55",
    # "markIv": "0.7567",
    # "underlyingPrice": "16590.42",
    # "openInterest": "6.3",
    # "turnover24h": "2482.73",
    # "volume24h": "0.15",
    # "totalVolume": "99",
    # "totalTurnover": "1967653",
    # "delta": "0.00000001",
    # "gamma": "0.00000001",
    # "vega": "0.00000004",
    # "theta": "-0.00000152",
    # "predictedDeliveryPrice": "0",
    # "change24h": "86"
    # endregion

    # region 查詢指定最新行情信息
    def get_specify_market_tickers(self, category, symbol):
        try:
            request = {
                'category' : category,
                'symbol'   : symbol
            }
            return self._session.publicGetV5MarketTickers(request)
        except BaseException as err:            
            raise Exception(f"An error occurred in function {__name__}: {err}") 
        
    # endregion

    # region 查詢歷史資金費率
    def get_orderbook(self, category, symbol, startTime, endTime, limit):
        try:
            request = {
                'category' : category,
                'symbol'   : symbol,
                'limit'    : limit   # 每頁數量限制. [1, 200]. 默認: 200
            }
            return self._session.publicGetV5MarketOrderbook(request)
        except BaseException as err:            
            raise Exception(f"An error occurred in function {__name__}: {err}")         
    # endregion

    # region 查詢期權波動率
    def get_historical_volatility(self, category, baseCoin, period, startTime, endTime):
        try:
            request = {
                'category'  : category,
                'baseCoin'  : baseCoin,
                'period'    : period,       # 週期. 不傳則默認返回7天加權的數據
                'startTime' : startTime,
                'endTime'   : endTime   
            }
            return self._session.get_historical_volatility(request)
        except BaseException as err:            
            raise Exception(f"An error occurred in function {__name__}: {err}")         
    # endregion

    # region 查詢多空比
    def get_account_ratio(self, category, symbol, period, limit):
        try:
            request = {
                'category' : category,
                'symbol'   : symbol,
                'period'   : period,
                'limit'    : limit     
            }
            return self._session.get_account_ratio(request)
        except BaseException as err:            
            raise Exception(f"An error occurred in function {__name__}: {err}")         
    # endregion

# endregion

# region 交易

    # region 查詢未平倉合約持倉數量
    def get_open_interest(self, category, symbol, intervalTime, startTime, endTime, limit, cursor):
        try:
            request = {
                'category'      : category,      # linear,inverse
                'symbol'        : symbol,
                'intervalTime'  : intervalTime,  # 時間粒度. 5min 15min 30min 1h 4h 1d
                'startTime'     : startTime,     # 到期日 ex: 25DEC22
                'endTime'       : endTime,       # 到期日 ex: 25DEC22
                'limit'         : limit,         # 每頁數量限制. [1, 200]. 默認: 50
                'cursor'        : cursor         # 游標，用於翻頁
            }

            result = pd.DataFrame(self._session.publicGetV5MarketOpenInterest(request))
            del result['timestamp']
            return result
        except BaseException as err:            
            raise Exception(f"An error occurred in function {__name__}: {err}") 

    #  Response ex
            # {
            #     "retCode": 0,
            #     "retMsg": "OK",
            #     "result": {
            #         "symbol": "BTCUSD",
            #         "category": "inverse",
            #         "list": [
            #             {
            #                 "openInterest": "461134384.00000000",
            #                 "timestamp": "1669571400000"
            #             },
            #             {
            #                 "openInterest": "461134292.00000000",
            #                 "timestamp": "1669571100000"
            #             }
            #         ],
            #         "nextPageCursor": ""
            #     },
            #     "retExtInfo": {},
            #     "time": 1672053548579
            # }

# endregion

    # region 創建委託單
    # @authentication_required
    # def createOrder(self, order_data):       
    #     try:
    #         return self._session.privatePostV5OrderCreate(order_data)
    #     except BaseException as err:
    #         raise Exception(f"An error occurred in function {__name__}: {err}") 

    # region Request ex
            # request = {
            #     'category'         : category,          # spot, linear, inverse, option
            #     'symbol'           : symbol,
            #     'isLeverage'       : isLeverage,        # 0(default): 否，則是幣幣訂單, 1: 是，則是槓桿訂單
            #     'side'             : side,              # buy or sell
            #     'orderType'        : orderType,         # market, limit
            #     'qty'              : qty,               # 開倉數量
            #     'marketUnit'       : marketUnit,
            #     'price'            : price,
            #     'triggerDirection' : triggerDirection,
            #     'orderFilter'      : orderFilter,       # Order、tpslOrder、StopOrder
            #     'triggerPrice'     : triggerPrice,
            #     'triggerBy'        : triggerBy,
            #     'orderIv'          : orderIv,
            #     'timeInForce'      : timeInForce,
            #     'positionIdx'      : positionIdx,
            #     'orderLinkId'      : orderLinkId,       # category=option時，該參數必傳
            #     'takeProfit'       : takeProfit,
            #     'stopLoss'         : stopLoss,
            #     'tpTriggerBy'      : tpTriggerBy,
            #     'slTriggerBy'      : slTriggerBy,
            #     'reduceOnly'       : reduceOnly,
            #     'closeOnTrigger'   : closeOnTrigger,
            #     'smpType'          : smpType,
            #     'mmp'              : mmp,
            #     'tpslMode'         : tpslMode,
            #     'tpLimitPrice'     : tpLimitPrice,
            #     'slLimitPrice'     : slLimitPrice,
            #     'tpOrderType'      : tpOrderType,
            #     'slOrderType'      : slOrderType
            # }

    # endregion


    # 產生現貨或合約訂單
    @authentication_required
    def create_order(self, category, symbol, side, orderType, qty, price, takeProfit, stopLoss):
        try:
            request = {
                'category'      : category,                                         # spot現貨、linear合約
                'symbol'        : symbol,
                'side'          : side,                                             # buy or sell
                'orderType'     : orderType,                                        # market, limit
                'qty'           : str(qty),                                         # 開倉數量
                'price'         : None if price == None else str(price),            # 市價免填
                'takeProfit'    : None if takeProfit == None else str(takeProfit),
                'stopLoss'      : None if takeProfit == None else str(stopLoss),
                'timeInForce'   : 'PostOnly',
                'orderFilter'   : 'Order'
            }
            return self.privatePostV5OrderCreate(self, request)
        except BaseException as err:
            raise Exception(f"An error occurred in function {__name__}: {err}")         

    # 產生期貨訂單
    @authentication_required
    def create_option_order(self, symbol, isLeverage, side, orderType, qty, price, triggerPrice,
        orderIv, timeInForce, orderLinkId, reduceOnly, closeOnTrigger, smpType, mmp):
        try:
            request = {
                'category'       : 'option',                                                # spot, linear, inverse, option
                'symbol'         : symbol,                                                  # BTC-26FEB24-48000-C 
                'isLeverage'     : isLeverage,                                              # 0(default): 否，則是幣幣訂單, 1: 是，則是槓桿訂單
                'side'           : side,                                                    # buy or sell
                'orderType'      : orderType,                                               # market, limit
                'qty'            : str(qty),                                                # 開倉數量
                'price'          : None if price == None else str(price),
                'triggerPrice'   : None if triggerPrice == None else str(triggerPrice),     # 對於期貨, 是條件單觸發價格參數. 若您希望市場價是要上升後觸發, 確保:triggerPrice > 市場價格否則, triggerPrice < 市場價格
                'orderIv'        : None if triggerPrice == None else str(orderIv),          # 隱含波動率 orderIv比price有更高的優先級
                'timeInForce'    : timeInForce,
                'orderLinkId'    : orderLinkId,                                             # category=option時，該參數必傳
                'reduceOnly'     : reduceOnly,                                              
                'closeOnTrigger' : closeOnTrigger,
                'smpType'        : smpType,                                                 # 自成交攔截CancelMaker、CancelTaker、CancelBoth 
                'mmp'            : mmp                                                      # 做市商保護bool
            }
            return self.privatePostV5OrderCreate(self, request)
        except BaseException as err:
            raise Exception(f"An error occurred in function {__name__}: {err}")              

    # endregion

    # region 修改委託單
    # endregion

# endregion

# region 持倉

    # region 查詢持倉(實時)
    @authentication_required
    def get_position(self, category, symbol=None):
        try :                            
            request = {
                'category'      : category,
                'symbol'        : symbol,
            }              
            result = self._session.privateGetV5PositionList(request)['result']['list'][0]
            position = {}
            for key, value in result.items():
                position[key] = value            
            # position = {
            #     'symbol'        : result['symbol'],
            #     'side'          : result['side'],
            #     'avgPrice'      : result['avgPrice'],
            #     'size'          : result['size'],
            #     'markPrice'     : result['markPrice'],
            #     'positionValue' : result['positionValue'],
            #     'createdTime'   : result['createdTime'],
            #     'updatedTime'   : result['updatedTime'],
            #     'stopLoss'      : result['stopLoss']
            # }            
            return position        
        except BaseException as err:
            raise Exception(f"An error occurred in function {__name__}: {err}") 

    # endregion

# endregion

# region 帳戶

    # region 取得錢包餘額
    @authentication_required
    def get_wallet_balance(self, coin=None):
        try:
            request = {
                "accountType":"UNIFIED",
                "coin": coin      
            }
            result = self._session.privateGetV5AccountWalletBalance(request)['result']['list'][0]['coin'][0]['availableToWithdraw']
            
            if result == None or  result == '':
                result = 0
            return result
        except BaseException as err:
            raise Exception(err)
    # endregion

# endregion

