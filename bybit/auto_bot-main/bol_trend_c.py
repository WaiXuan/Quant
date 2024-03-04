import sys
sys.path.append("./auto_bot")
import ccxt
import ta
import pandas as pd
from perp_bybit import PerpBybit
from custom_indicator import get_n_columns
from datetime import datetime
import time
import json

# 現在時間
now = datetime.now()
current_time = now.strftime("%d/%m/%Y %H:%M:%S")
print("--- 開始執行時間：", current_time, "---")

# 讀取金鑰
f = open("/home/ubuntu/auto_bot/secret.json")
secret = json.load(f)
f.close()

# 選擇帳戶並設定環境
account_to_select = "bybit_exemple"
production = True

# 設定交易對、時間框架、槓桿、倍數和停損百分比
pair = "ETH/USDT:USDT"
timeframe = "1h"
leverage = 0.35
mult = 5
percent_sl = -0.35

# 定義交易方向
type = ["long", "short"]

# 定義指標參數
bol_window = 100
bol_std = 2.25
min_bol_spread = 0
long_ma_window = 900

# 開多倉判斷條件
def open_long(row):
    if (
        (row['n1_close'] < row['n1_higher_band'])
        and  (row['close'] > row['higher_band'])
        and  ((row['n1_higher_band'] - row['n1_lower_band']) / row['n1_lower_band'] > min_bol_spread)
        and (row['close'] > row['long_ma'])
    ):
        return True
    else:
        return False

# 平多倉判斷條件
def close_long(row):
    if (row['close'] < row['ma_band']):
        return True
    else:
        return False

# 開空倉判斷條件
def open_short(row):
    if (
        row['n1_close'] > row['n1_lower_band']
        and (row['close'] < row['lower_band'])
        and ((row['n1_higher_band'] - row['n1_lower_band']) / row['n1_lower_band'] > min_bol_spread)
        and (row['close'] < row['long_ma'])
    ):
        return True
    else:
        return False

# 平空倉判斷條件
def close_short(row):
    if (row['close'] > row['ma_band']):
        return True
    else:
        return False

# 連接 Bybit API
bybit = PerpBybit(
    apiKey=secret[account_to_select]["apiKey"],
    secret=secret[account_to_select]["secret"],
)

# 獲取歷史數據
df = bybit.get_more_last_historical_async(pair, timeframe, 1000)

# 提取指標數據
df.drop(columns=df.columns.difference(['open','high','low','close','volume']), inplace=True)
bol_band = ta.volatility.BollingerBands(close=df["close"], window=bol_window, window_dev=bol_std)
df["lower_band"] = bol_band.bollinger_lband()
df["higher_band"] = bol_band.bollinger_hband()
df["ma_band"] = bol_band.bollinger_mavg()
df['long_ma'] = ta.trend.sma_indicator(close=df['close'], window=long_ma_window)
df = get_n_columns(df, ["ma_band", "lower_band", "higher_band", "close"], 1)

# 獲取 USD 餘額
usd_balance = float(bybit.get_usdt_equity())
print("USD 餘額：", round(usd_balance, 2), "$")

# 獲取持倉信息
positions_data = bybit.get_open_position()
position = [
    {"side": d["side"], "size": d["contractSize"], "market_price":d["markPrice"], "usd_size": float(d["contractSize"]) * float(d["markPrice"]), "open_price": d["entryPrice"]}
    for d in positions_data if d["symbol"] == pair]
row = df.iloc[-2]

# 判斷是否有持倉
if len(position) > 0:
    position = position[0]
    print(f"目前持倉：{position}")
    if position["side"] == "long" and close_long(row):
        close_long_market_price = float(df.iloc[-1]["close"])
        close_long_quantity = float(
            bybit.convert_amount_to_precision(pair, position["size"])
        )
        exchange_close_long_quantity = close_long_quantity * close_long_market_price
        print(
            f"下單平多倉市價單：{close_long_quantity} {pair[:-5]}，價格為 {close_long_market_price}$，約值約 {round(exchange_close_long_quantity, 2)}$"
        )
        if production:
            bybit.place_market_order(pair, "sell", close_long_quantity, reduce=True)

    elif position["side"] == "short" and close_short(row):
        close_short_market_price = float(df.iloc[-1]["close"])
        close_short_quantity = float(
            bybit.convert_amount_to_precision(pair, position["size"])
        )
        exchange_close_short_quantity = close_short_quantity * close_short_market_price
        print(
            f"下單平空倉市價單：{close_short_quantity} {pair[:-5]}，價格為 {close_short_market_price}$，約值約 {round(exchange_close_short_quantity, 2)}$"
        )
        if production:
            bybit.place_market_order(pair, "buy", close_short_quantity, reduce=True)

else:
    print("無持倉")
    if open_long(row) and "long" in type:
        long_market_price = float(df.iloc[-1]["close"])
        long_quantity_in_usd = usd_balance * leverage * mult
        long_quantity = float(bybit.convert_amount_to_precision(pair, float(
            bybit.convert_amount_to_precision(pair, long_quantity_in_usd / long_market_price)
        )))
        exchange_long_quantity = long_quantity * long_market_price
        print(
            f"下單開多倉市價單：{long_quantity} {pair[:-5]}，價格為 {long_market_price}$，約值約 {round(exchange_long_quantity, 2)}$"
        )
        if production:
            trigger_price = (( percent_sl * long_market_price ) + ( long_market_price * mult ))/mult
            bybit.place_market_stop_loss(pair, "buy", long_quantity, trigger_price, reduce=False)

    elif open_short(row) and "short" in type:
        short_market_price = float(df.iloc[-1]["close"])
        short_quantity_in_usd = usd_balance * leverage * mult
        short_quantity = float(bybit.convert_amount_to_precision(pair, float(
            bybit.convert_amount_to_precision(pair, short_quantity_in_usd / short_market_price)
        )))
        exchange_short_quantity = short_quantity * short_market_price
        print(
            f"下單開空倉市價單：{short_quantity} {pair[:-5]}，價格為 {short_market_price}$，約值約 {round(exchange_short_quantity, 2)}$"
        )
        if production:
            trigger_price = (( short_market_price * mult )-( percent_sl * short_market_price ))/ mult
            bybit.place_market_stop_loss(pair, "sell", short_quantity, trigger_price, reduce=False)

# 結束執行時間
now = datetime.now()
current_time = now.strftime("%d/%m/%Y %H:%M:%S")
print("--- 結束執行時間：", current_time, "---")
print("n1_close:",row['n1_close']," n1_Higer_Bol:", row['n1_higher_band']," close:", row['close'], " HigherBol:", row['higher_band'], " MA:", row["long_ma"])
