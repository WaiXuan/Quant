import ccxt
import pandas as pd
import time
from multiprocessing.pool import ThreadPool as Pool
import numpy as np

class PerpBybit():
    def __init__(self, apiKey=None, secret=None):
        # 初始化 PerpBybit 類別，接收 apiKey 和 secret 作為參數
        bybit_auth_object = {
            "apiKey": apiKey,
            "secret": secret,
            'options': {
                'defaultType': 'swap',
            }
        }
        if bybit_auth_object['secret'] == None:
            self._auth = False
            self._session = ccxt.bybit()
        else:
            self._auth = True
            self._session = ccxt.bybit(bybit_auth_object)
        self.market = self._session.load_markets()

    def authentication_required(fn):
        """需要驗證的方法的註解"""
        def wrapped(self, *args, **kwargs):
            if not self._auth:
                # 如果尚未驗證則拋出例外
                raise Exception("您必須通過驗證才能使用此方法")
            else:
                # 如果已驗證，則執行原始方法
                return fn(self, *args, **kwargs)
        return wrapped

    def get_last_historical(self, symbol, timeframe, limit):
        # 獲取最後幾筆歷史數據的方法，接收交易對、時間間隔和限制數量作為參數
        result = pd.DataFrame(data=self._session.fetch_ohlcv(
            symbol, timeframe, None, limit=limit))
        result = result.rename(
            columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'})
        result = result.set_index(result['timestamp'])
        result.index = pd.to_datetime(result.index, unit='ms')
        del result['timestamp']
        return result

    def get_more_last_historical_async(self, symbol, timeframe, limit):
        # 非同步獲取更多最後幾筆歷史數據的方法，接收交易對、時間間隔和限制數量作為參數
        max_threads = 4
        pool_size = round(limit/100)  # 控制平行度的變量

        # 在創建 Pool 之前定義 worker 函數
        full_result = []
        def worker(i):
            try:
                return self._session.fetch_ohlcv(
                symbol, timeframe, round(time.time() * 1000) - (i*1000*60*60), limit=100)
            except Exception as err:
                raise Exception("在 " + symbol + " 上獲取最後幾筆歷史數據時發生錯誤: " + str(err))

        pool = Pool(max_threads)

        full_result = pool.map(worker,range(limit, 0, -100))
        full_result = np.array(full_result).reshape(-1,6)
        result = pd.DataFrame(data=full_result)
        result = result.rename(
            columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'})
        result = result.set_index(result['timestamp'])
        result.index = pd.to_datetime(result.index, unit='ms')
        del result['timestamp']
        return result.sort_index()

    # 獲取 合約帳戶 USDT 餘額
    @authentication_required
    def get_usdt_equity(self):
        try:
            usdt_equity = self._session.fetch_balance({'coin':'USDT' })["info"]['result']['list'][0]['equity']
        except BaseException as err:
            raise Exception("發生錯誤", err)
        try:
            return usdt_equity
        except:
            return 0


    # 獲取已開倉倉位
    @authentication_required
    def get_open_position(self,symbol=None):
        try:
            positions = self._session.fetch_positions(symbol)
            truePositions = []
            for position in positions:
                if float(position['contractSize']) > 0:
                    truePositions.append(position)
            return truePositions
        except BaseException as err:
            raise TypeError("在get_open_position中發生錯誤", err)

    def convert_amount_to_precision(self, symbol, amount):
        # 將數量轉換為精度的方法
        return self._session.amount_to_precision(symbol, amount)

    @authentication_required
    def place_market_order(self, symbol, side, amount, reduce=False):
        # 下市價單的方法
        try:
            return self._session.create_order(
                symbol,
                'market',
                side,
                self.convert_amount_to_precision(symbol, amount),
                None,
                params = {'reduce_only': reduce},
            )
        except BaseException as err:
            raise Exception(err)

    # 下市價止損單的方法
    @authentication_required
    def place_market_stop_loss(self, symbol, side, amount, trigger_price, reduce=False):
        try:
            return self._session.create_order(
                symbol,
                'market',
                side,
                self.convert_amount_to_precision(symbol, amount),
                self.convert_price_to_precision(symbol, trigger_price),
                params = {
                    'stop_loss': self.convert_price_to_precision(symbol, trigger_price),  # 止損價格
                    "triggerType": "market_price",
                    "reduce_only": reduce
                },
            )
        except BaseException as err:
            raise Exception(err)

    # 將價格轉換為精度的方法
    def convert_price_to_precision(self, symbol, price):
        return self._session.price_to_precision(symbol, price)
