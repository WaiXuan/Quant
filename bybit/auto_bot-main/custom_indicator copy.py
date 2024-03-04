import math
import numpy as np
import pandas as pd
import ta
import math
import requests


def chop(high, low, close, window=14):
    ''' Choppiness indicator
    '''
    # 計算每個bar的真實範圍
    tr1 = pd.DataFrame(high - low).rename(columns={0: 'tr1'})
    # 計算high和前一根bar的close的絕對值
    tr2 = pd.DataFrame(abs(high - close.shift(1))).rename(columns={0: 'tr2'})
    # 計算low和前一根bar的close的絕對值
    tr3 = pd.DataFrame(abs(low - close.shift(1))).rename(columns={0: 'tr3'})
    # 將三個DataFrame合併為一個DataFrame，並選擇最大值
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').dropna().max(axis=1)
    # 計算平均真實範圍
    atr = tr.rolling(1).mean()
    # 計算窗口內的最高價格
    highh = high.rolling(window).max()
    # 計算窗口內的最低價格
    lowl = low.rolling(window).min()
    # 計算Choppiness指標
    chop_serie = 100 * np.log10((atr.rolling(window).sum()) / (highh - lowl)) / np.log10(window)
    return pd.Series(chop_serie, name="CHOP")


def fear_and_greed(close):
    ''' Fear and greed indicator
    '''
    # 從API獲取Fear and Greed指標數據
    response = requests.get("https://api.alternative.me/fng/?limit=0&format=json")
    dataResponse = response.json()['data']
    fear = pd.DataFrame(dataResponse, columns=['timestamp', 'value'])

    fear = fear.set_index(fear['timestamp'])
    fear.index = pd.to_datetime(fear.index, unit='s')
    del fear['timestamp']
    df = pd.DataFrame(close, columns=['close'])
    df['fearResult'] = fear['value']
    df['FEAR'] = df['fearResult'].ffill()
    df['FEAR'] = df.FEAR.astype(float)
    return pd.Series(df['FEAR'], name="FEAR")


class Trix():
    """ Trix指標
        Args:
            close(pd.Series): dataframe 'close' column,
            trixLength(int): trix每個移動平均的窗口長度,
            trixSignal(int): signal線的窗口長度
    """
    def __init__(
        self,
        close: pd.Series,
        trixLength: int = 9,
        trixSignal: int = 21
    ):
        self.close = close
        self.trixLength = trixLength
        self.trixSignal = trixSignal
        self._run()

    def _run(self):
        # 計算trix line
        self.trixLine = ta.trend.ema_indicator(
            ta.trend.ema_indicator(
                ta.trend.ema_indicator(
                    close=self.close, window=self.trixLength),
                window=self.trixLength),
            window=self.trixLength),
        window=self.trixLength)

        # 計算signal line
        self.signalLine = ta.trend.ema_indicator(
            ta.trend.ema_indicator(
                ta.trend.ema_indicator(
                    close=self.close, window=self.trixLength),
                window=self.trixLength),
            window=self.trixSignal)

        # 計算trix histogram
        self.histogram = self.trixLine - self.signalLine

def trix_line(self) -> pd.Series:
    """trix線
    返回：
        pd.Series：trix線
    """
    return pd.Series(self.trixLine, name="TRIX_LINE")

def trix_pct_line(self) -> pd.Series:
    """trix百分比線
    返回：
        pd.Series：trix百分比線
    """
    return pd.Series(self.trixPctLine, name="TRIX_PCT_LINE")

def trix_signal_line(self) -> pd.Series:
    """trix信號線
    返回：
        pd.Series：trix信號線
    """
    return pd.Series(self.trixSignal, name="TRIX_SIGNAL_LINE")

def trix_histo(self) -> pd.Series:
    """trix直方圖
    返回：
        pd.Series：trix直方圖
    """
    return pd.Series(self.trixHisto, name="TRIX_HISTO")

class VMC():
    """VuManChu Cipher B + Divergences
    參數：
        high(pandas.Series)：數據集的'High'列。
        low(pandas.Series)：數據集的'Low'列。
        close(pandas.Series)：數據集的'Close'列。
        wtChannelLen(int)：n期間。
        wtAverageLen(int)：n期間。
        wtMALen(int)：n期間。
        rsiMFIperiod(int)：n期間。
        rsiMFIMultiplier(int)：n期間。
        rsiMFIPosY(int)：n期間。
    """
    def __init__(
        self: pd.Series,
        open: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        wtChannelLen: int = 9,
        wtAverageLen: int = 12,
        wtMALen: int = 3,
        rsiMFIperiod: int = 60,
        rsiMFIMultiplier: int = 150,
        rsiMFIPosY: int = 2.5
    ) -> None:
        self._high = high
        self._low = low
        self._close = close
        self._open = open
        self._wtChannelLen = wtChannelLen
        self._wtAverageLen = wtAverageLen
        self._wtMALen = wtMALen
        self._rsiMFIperiod = rsiMFIperiod
        self._rsiMFIMultiplier = rsiMFIMultiplier
        self._rsiMFIPosY = rsiMFIPosY

        self._run()
        self.wave_1()

    def _run(self) -> None:
        self.hlc3 = (self._close + self._high + self._low)
        self._esa = ta.trend.ema_indicator(
            close=self.hlc3, window=self._wtChannelLen)
        self._de = ta.trend.ema_indicator(
            close=abs(self.hlc3 - self._esa), window=self._wtChannelLen)
        self._rsi = ta.trend.sma_indicator(self._close, self._rsiMFIperiod)
        self._ci = (self.hlc3 - self._esa) / (0.015 * self._de)

def wave_1(self) -> pd.Series:
    """VMC Wave 1 
    返回：
        pd.Series：生成的新特徵
    """
    wt1 = ta.trend.ema_indicator(self._ci, self._wtAverageLen)
    return pd.Series(wt1, name="wt1")

def wave_2(self) -> pd.Series:
    """VMC Wave 2
    返回：
        pd.Series：生成的新特徵
    """
    wt2 = ta.trend.sma_indicator(self.wave_1(), self._wtMALen)
    return pd.Series(wt2, name="wt2")

def money_flow(self) -> pd.Series:
    """VMC Money Flow
    返回：
        pd.Series：生成的新特徵
    """
    mfi = ((self._close - self._open) /
           (self._high - self._low)) * self._rsiMFIMultiplier
    rsi = ta.trend.sma_indicator(mfi, self._rsiMFIperiod)
    money_flow = rsi - self._rsiMFIPosY
    return pd.Series(money_flow, name="money_flow")


def heikinAshiDf(df):
    df['HA_Close'] = (df.open + df.high + df.low + df.close)/4
    ha_open = [(df.open[0] + df.close[0]) / 2]
    [ha_open.append((ha_open[i] + df.HA_Close.values[i]) / 2)
     for i in range(0, len(df)-1)]
    df['HA_Open'] = ha_open
    df['HA_High'] = df[['HA_Open', 'HA_Close', 'high']].max(axis=1)
    df['HA_Low'] = df[['HA_Open', 'HA_Close', 'low']].min(axis=1)
    return df


def volume_anomality(df, volume_window=10):
    dfInd = df.copy()
    dfInd["VolAnomaly"] = 0
    dfInd["PreviousClose"] = dfInd["close"].shift(1)
    dfInd['MeanVolume'] = dfInd['volume'].rolling(volume_window).mean()
    dfInd['MaxVolume'] = dfInd['volume'].rolling(volume_window).max()
    dfInd.loc[dfInd['volume'] > 1.5 * dfInd['MeanVolume'], "VolAnomaly"] = 1
    dfInd.loc[dfInd['volume'] > 2 * dfInd['MeanVolume'], "VolAnomaly"] = 2
    dfInd.loc[dfInd['volume'] >= dfInd['MaxVolume'], "VolAnomaly"] = 3
    dfInd.loc[dfInd['PreviousClose'] > dfInd['close'],
              "VolAnomaly"] = (-1) * dfInd["VolAnomaly"]
    return dfInd["VolAnomaly"]

class SuperTrend():
    def __init__(
        self,
        high,
        low,
        close,
        atr_window=10,
        atr_multi=3
    ):
        self.high = high
        self.low = low
        self.close = close
        self.atr_window = atr_window
        self.atr_multi = atr_multi
        self._run()
        
    def _run(self):
        # 計算ATR
        price_diffs = [self.high - self.low, 
                    self.high - self.close.shift(), 
                    self.close.shift() - self.low]
        true_range = pd.concat(price_diffs, axis=1)
        true_range = true_range.abs().max(axis=1)
        # Supertrend指標中的預設ATR計算
        atr = true_range.ewm(alpha=1/self.atr_window,min_periods=self.atr_window).mean() 
        
        # HL2價格是最高價和最低價的平均值
        hl2 = (self.high + self.low) / 2
        # 上界和下界的計算
        # 注意最終的界限被設置為相應的界限
        final_upperband = upperband = hl2 + (self.atr_multi * atr)
        final_lowerband = lowerband = hl2 - (self.atr_multi * atr)
        
        # 初始化Supertrend列為True
        supertrend = [True] * len(self.close)
        
        for i in range(1, len(self.close)):
            curr, prev = i, i-1
            
            # 如果當前收盤價上穿上界
            if self.close[curr] > final_upperband[prev]:
                supertrend[curr] = True
            # 如果當前收盤價下穿下界
            elif self.close[curr] < final_lowerband[prev]:
                supertrend[curr] = False
            # 否則，趨勢繼續
            else:
                supertrend[curr] = supertrend[prev]
                
                # 對最終界限進行調整
                if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                    final_lowerband[curr] = final_lowerband[prev]
                if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                    final_upperband[curr] = final_upperband[prev]

            # 根據趨勢方向刪除界限
            if supertrend[curr] == True:
                final_upperband[curr] = np.nan
            else:
                final_lowerband[curr] = np.nan
                
        self.st = pd.DataFrame({
            'Supertrend': supertrend,
            'Final Lowerband': final_lowerband,
            'Final Upperband': final_upperband
        })
        
    def super_trend_upper(self):
        return self.st['Final Upperband']
        
    def super_trend_lower(self):
        return self.st['Final Lowerband']
        
    def super_trend_direction(self):
        return self.st['Supertrend']
    
class MaSlope():
    """ 坡度適應移動平均線
    """
    def __init__(
        self,
        close: pd.Series,
        high: pd.Series,
        low: pd.Series,
        long_ma: int = 200,
        major_length: int = 14,
        minor_length: int = 6,
        slope_period: int = 34,
        slope_ir: int = 25
    ):
        self.close = close
        self.high = high
        self.low = low
        self.long_ma = long_ma
        self.major_length = major_length
        self.minor_length = minor_length
        self.slope_period = slope_period
        self.slope_ir = slope_ir
        self._run()

    def _run(self):
        minAlpha = 2 / (self.minor_length + 1)
        majAlpha = 2 / (self.major_length + 1)
        df = pd.DataFrame(data = {"close": self.close, "high": self.high, "low":self.low})
        df['hh'] = df['high'].rolling(window=self.long_ma+1).max()
        df['ll'] = df['low'].rolling(window=self.long_ma+1).min()
        df = df.fillna(0)
        df.loc[df['hh'] == df['ll'],'mult'] = 0
        df.loc[df['hh'] != df['ll'],'mult'] = abs(2 * df['close'] - df['ll'] - df['hh']) / (df['hh'] - df['ll'])
        df['final'] = df['mult'] * (minAlpha - majAlpha) + majAlpha

        ma_first = (df.iloc[0]['final']**2) * df.iloc[0]['close']

        col_ma = [ma_first]
        for i in range(1, len(df)):
            ma1 = col_ma[i-1]
            col_ma.append(ma1 + (df.iloc[i]['final']**2) * (df.iloc[i]['close'] - ma1))

        df['ma'] = col_ma
        pi = math.atan(1) * 4
        df['hh1'] = df['high'].rolling(window=self.slope_period).max()
        df['ll1'] = df['low'].rolling(window=self.slope_period).min()
        df['slope_range'] = self.slope_ir / (df['hh1'] - df['ll1']) * df['ll1']
        df['dt'] = (df['ma'].shift(2) - df['ma']) / df['close'] * df['slope_range'] 
        df['c'] = (1+df['dt']*df['dt'])**0.5
        df['xangle'] = round(180*np.arccos(1/df['c']) / pi)
        df.loc[df['dt']>0,"xangle"] = - df['xangle']
        self.df = df

    def ma_line(self) -> pd.Series:
        """ 移動平均線
            Returns:
                pd.Series: 移動平均線
        """
        return self.df['ma']

    def x_angle(self) -> pd.Series:
        """ x角度
            Returns:
                pd.Series: x角度
        """
        return self.df['xangle']
    
def get_n_columns(df, columns, n=1):
    dt = df.copy()
    for col in columns:
        dt["n"+str(n)+"_"+col] = dt[col].shift(n)
    return dt
