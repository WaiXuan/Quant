# -*- coding: utf-8 -*-
import ccxt
import pandas as pd
import datetime
import threading
from time import sleep
import requests

long_sleep_time = 0
# 跟單倍數
follow_trading = 4
# 創建OKEx交易所對象
proxy = ''
#proxy = {'http': 'http://127.0.0.1:10100', 'https': '127.0.0.1:10100'}

# okex交易所配置
okex_exchange = ccxt.okx({
    'apiKey': '',
    'secret': '',
    'password': 'Kao@851029',
    'timeout': 3000,
    'rateLimit': 10,
    'proxies': proxy,
    'enableRateLimit': False})

# 創建 Bitget 交易所對象
bitget_track_exchange = ccxt.bitget({
    'apiKey': '',
    'secret': '',
    'password' : 'kaoweixuan',
    'enableRateLimit': True,  # 啟用請求限制
    'proxies': proxy,
})

# 封裝交易所symbol格式
def get_okex_positions(symbol):
    inst_id = f'{symbol}-USDT-SWAP'
    return inst_id

def get_bitget_positions(symbol):
    umcbl_symbol = f'{symbol}USDT'
    return umcbl_symbol

# bitget帶單員平倉函數
def bg_close_position(bitget_track_exchange, symbol, holdSide):
    bg_order_response = bitget_track_exchange.privateMixPostV2MixOrderClosePositions({
            'symbol': symbol,
            'productType': 'USDT-FUTURES',
            'holdSide': holdSide
    })

    # 判斷平倉是否成功
    if 'code' in bg_order_response and bg_order_response['code'] == '00000':
        print('平倉成功！')
        # 在這裡可以繼續處理平倉成功後的邏輯
        return True
    else:
        print('平倉失敗！')
        # 輸出錯誤信息
        print('錯誤信息:', bg_order_response.get('msg', '未提供錯誤信息'))
        return False

# 輔助函數處理下單響應
def handle_order_response(order_response):
    if 'code' in order_response and order_response['code'] == '00000':
        print('下單成功！')
        # 在這裡可以繼續處理下單成功後的邏輯
    else:
        print('下單失敗！')
        print('錯誤信息:', order_response.get('msg', '未提供錯誤信息'))

# 币种同步主函數
def main(ok_trades, bitget_positions, bitget_track_exchange, symbol, size):
    # 鎖定線程，確保打印輸出不會交織
    # with print_lock:
        total_open_deal_count_OK_long = 0
        total_open_deal_count_bg_long = 0
        total_open_deal_count_OK_short = 0
        total_open_deal_count_bg_short = 0
        # 獲取OK跟單帳戶持倉信息,函數外面直接獲取 ok API 是2s 10次 每個幣種都抓不夠用
        # 如果有數據就計算
        if ok_trades['data']:
            # 提取 instId 和 availPos 字段
            selected_OK_trades = [{'交易對': item['instId'], '方向': item['posSide'], 'ID': item['posId'], '持倉數量': item['pos']} for item in ok_trades['data']]

            # 創建DataFrame
            positions_OK = pd.DataFrame(selected_OK_trades)
            # ok交易所的幣跟張數轉換 重要 重要 重要
            positions_OK['持倉數量'] = positions_OK['持倉數量'].astype(float) * size

            # 計算OK的倉位數量
            # 過濾出當下 symbol 方向數據
            positions_OK = positions_OK[positions_OK['交易對'] == get_okex_positions(symbol)]
            # 過濾出long方向數據
            long_positions_OK = positions_OK[positions_OK['方向'] == 'long']
            # 統計long倉位總數
            total_open_deal_count_OK_long = long_positions_OK['持倉數量'].astype(float).sum()
            if total_open_deal_count_OK_long > 0:
                print(long_positions_OK)
                print(f'OK LONG {symbol}總持倉數量:', total_open_deal_count_OK_long)
            # 過濾出 short 方向數據
            short_positions_OK = positions_OK[positions_OK['方向'] == 'short']
            # 統計 short 倉位總數
            total_open_deal_count_OK_short = short_positions_OK['持倉數量'].astype(float).sum()
            if total_open_deal_count_OK_short > 0:
                print(short_positions_OK)
                print(f'OK short {symbol}總持倉數量:', total_open_deal_count_OK_short)
        else:
            print(f'OK {symbol}沒有持倉')

        # 獲取bitget帶單帳戶持倉信息,函數裡面根據交易對獲取,bitget跟單接口只能指定幣種獲取 1s 10次
        # TODO 調整成外傳入持倉信息
        #positions = bitget_track_exchange.privateMixGetV2MixPositionSinglePosition({ 'symbol': get_bitget_positions(symbol), 'marginCoin' : 'USDT', 'productType':'USDT-FUTURES'})
        positions = bitget_positions
        # 如果有數據
        if positions['data']:
            selected_bg_trades = [{'交易對': item['symbol'], '方向': item['holdSide'], '持倉數量': item['total']} for item in positions['data']]
            positions_bg = pd.DataFrame(selected_bg_trades)
            pd.set_option('display.max_columns', None)
            # 計算bitget的倉位數量

            # 過濾出當下 symbol 方向數據
            positions_bg = positions_bg[positions_OK['交易對'] == get_bitget_positions(symbol)]            
            
            # 過濾出 long 方向數據
            long_positions_bg = positions_bg[positions_bg['方向'] == 'long']
            # 統計 long 持倉
            total_open_deal_count_bg_long = long_positions_bg['持倉數量'].astype(float).sum()
            if not long_positions_bg.empty:
                print(f'BITGET LONG {symbol}總持倉數量:', total_open_deal_count_bg_long)
                print(long_positions_bg)
            # 過濾出 short 方向數據
            short_positions_bg = positions_bg[positions_bg['方向'] == 'short']
            # 統計 short 持倉
            total_open_deal_count_bg_short = short_positions_bg['持倉數量'].astype(float).sum()
            if not short_positions_bg.empty:
                print(f'BITGET short {symbol}總持倉數量:', total_open_deal_count_bg_short)
                print(short_positions_bg)
        else:
            print(f'bitget 沒有 {symbol} 持倉')

        #exit('測試數據不能真正下單')
        # 判斷是否需要進行同步
        if ok_trades['code'] == '0' and positions['msg'] == 'success':
            # 多頭
            if total_open_deal_count_OK_long != total_open_deal_count_bg_long / follow_trading:  # 計算需要跟單倍數
                # 計算差值
                quantity_diff = total_open_deal_count_OK_long - total_open_deal_count_bg_long / follow_trading
                # print(quantity_diff)
                if quantity_diff > 0:
                    # 需要加倉到 Bitget
                    # 下單數量
                    order_size = quantity_diff * follow_trading
                    print(f'需要加倉到 Bitget:加倉數量為 {order_size}，同步倍數{follow_trading}')
                    # 檢查下單數量
                    # TODO 取得下單最小數額
                    if order_size >= size:
                        # 下單數量
                        # ############################ bitget正式下單 ##############################
                        bg_order_response = bitget_track_exchange.privateMixPostV2MixOrderPlaceOrder({
                            'symbol': get_bitget_positions(symbol),
                            'productType': 'USDT-FUTURES',
                            'marginMode': 'crossed',
                            'marginCoin': 'USDT',
                            'size': order_size,
                            'orderType': 'market',
                            'side': 'buy',
                            'tradeSide' : 'open'
                        })       
                                                
                        handle_order_response(bg_order_response) # 判斷下單是否成功
                    else:
                        print(f'long {symbol}開單數量太小，不做處理{order_size}')
                else:
                    # 需要減倉從 Bitget
                    print(f'正在 Long 平倉{symbol}從 Bitget:平倉數量為 {-quantity_diff}')
                    if total_open_deal_count_OK_long == 0 :
                        bg_close_position(bitget_track_exchange, get_bitget_positions(symbol), 'long')
                    else:
                        bg_order_response = bitget_track_exchange.privateMixPostV2MixOrderPlaceOrder({
                            'symbol': get_bitget_positions(symbol),
                            'productType': 'USDT-FUTURES',
                            'marginMode': 'crossed',
                            'marginCoin': 'USDT',
                            'size': (quantity_diff *-1),
                            'orderType': 'market',
                            'side': 'buy',
                            'tradeSide' : 'close'
                        })              
                        handle_order_response(bg_order_response)   
            else:
                print(f'OKEx 和 Bitget 的 long {symbol}持倉數量已經同步')

            # 空頭
            if total_open_deal_count_OK_short != total_open_deal_count_bg_short/follow_trading: # 計算需要跟單倍數
                # 計算差值
                quantity_diff = total_open_deal_count_OK_short - total_open_deal_count_bg_short/follow_trading
                # print(quantity_diff)
                if quantity_diff > 0:
                    # 需要加倉到 Bitget
                    print(f'short 需要到 Bitget:開空的數量為 {quantity_diff}')
                    # 下單數量
                    order_size = quantity_diff * follow_trading
                    # 檢查下單數量
                    if order_size >= size:
                        print(f'正在bitget 開short單:數量為 {order_size}，同步倍數{follow_trading}')
                        # ############################ 正式下單 ##############################
                        # 執行加倉操作 private_mix_post_order_placeorder
                        
                        bg_order_response = bitget_track_exchange.privateMixPostV2MixOrderPlaceOrder({
                            'symbol': get_bitget_positions(symbol),
                            'productType': 'USDT-FUTURES',
                            'marginMode': 'crossed',
                            'marginCoin': 'USDT',
                            'size': order_size,
                            'orderType': 'market',
                            'side': 'sell',
                            'tradeSide' : 'open'
                        })                        
                        # 判斷下單是否成功
                        handle_order_response(bg_order_response)
                else:
                    # 需要平倉從 Bitget
                    print(f'正在 short 平倉{symbol}從 Bitget:平倉數量為 {-quantity_diff}')
                    if total_open_deal_count_OK_short == 0 :
                        bg_close_position(bitget_track_exchange, get_bitget_positions(symbol), 'short')
                    else:
                        bg_order_response = bitget_track_exchange.privateMixPostV2MixOrderPlaceOrder({
                            'symbol': get_bitget_positions(symbol),
                            'productType': 'USDT-FUTURES',
                            'marginMode': 'crossed',
                            'marginCoin': 'USDT',
                            'size': (quantity_diff *-1),
                            'orderType': 'market',
                            'side': 'sell',
                            'tradeSide' : 'close'
                        })              
                        handle_order_response(bg_order_response)          
            else:
                print(f'OKEx 和 Bitget 的 short {symbol}持倉數量已經同步')

        else:
            print('api有獲取失敗行為,不做同步處理')
        # 本幣種主體同步邏輯結束

        # 格式化當前時間為字符串
        formatted_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 打印帶有當前時間的消息
        print('\n', '-' * long_sleep_time, f'{symbol}同步結束，當前時間:{formatted_time}', '-' * long_sleep_time, '\n\n')
        sleep(long_sleep_time)

# 發送Line訊息        
def send_line_message(message) :       
    # HTTP 標頭參數與資料
    key='hoHscFvVDHkbX8oFdyXc7gl9kkVHqCG6uOUzVJcp6OO'
    headers = { 'Authorization': 'Bearer ' + key }
    data = { 'message': message }
    # 以 requests 發送 POST 請求
    try :
        requests.post('https://notify-api.line.me/api/notify',
            headers = headers, data = data)
        pass
    except BaseException as err:
        print(err) 

if __name__ == '__main__':
    # symbols = ['BTC', 'ETH', 'SOL', 'ORDI']  # 要處理的幣種列表
    # symbol_min_size = {
    #     'BTC': 0.01,
    #     'ETH': 0.1,
    #     'SOL': 1,
    #     'ORDI': 0.1
    #     # 添加其他幣種的最小下單數量
    # }
    print_lock = threading.Lock() # 創建線程鎖對象
    max_retries = 100  # 設置最大重試次數
    consecutive_failures = 0  # 初始化當前重試次數
    while consecutive_failures < max_retries:
        try:
            # ok可以所有幣種先爬出來
            # 獲取OK跟他人單倉位明細(跟單倉位)
            ok_positions = okex_exchange.private_get_copytrading_current_subpositions({'instType':'SWAP'})

            # 獲取bg跟自己單倉位明細(一般倉位)
            bg_positions = bitget_track_exchange.privateMixGetV2MixPositionAllPosition({'productType':'USDT-FUTURES', 'marginCoin':'USDT'})

            # 統整須比對幣種
            symbols = [data['symbol'][:data['symbol'].index('USDT')] for data in bitget_positions['data']]
            inst_ids = [data['instId'][:data['instId'].index('-USDT')] for data in ok_positions['data']]
            unique_symbols = list(set(inst_ids + symbols))            

            symbol_min_size = {}
            # 取得所有幣種的最小下單數量
            for item in bitget_track_exchange.publicMixGetV2MixMarketContracts({'productType':'USDT-FUTURES'})['data']:
                base_coin = item['baseCoin']
                if base_coin in unique_symbols:
                    symbol_min_size[base_coin] = item['sizeMultiplier']
            # 计算最小投资数量

            # 获取交易产品基础信息 GET /api/v5/public/instruments
            okex_exchange.publicGetV5MarketTickers({'instType':'SWAP'})


            threads = []  # 創建線程列表
            for symbol in unique_symbols:
                size = symbol_min_size.get(symbol, 1)
                # thread = threading.Thread(target=main, args=(ok_positions, bitget_positions, bitget_track_exchange, symbol, size))
                # threads.append(thread)
                # thread.start()
                main(ok_positions, bitget_positions, bitget_track_exchange, symbol, size)
            # 等待所有線程完成
            for thread in threads:
                thread.join()
            # 如果成功運行完所有幣種，重置連續失敗次數
            consecutive_failures = 0
        except Exception as e:
            consecutive_failures += 1
            print(f'Exception occurred: {e}')
            send_line_message(f'Exception occurred: {e}')
            if consecutive_failures < max_retries:
                print(f'Retrying... (Retry {consecutive_failures} of {max_retries})')
                sleep(long_sleep_time)
            else:
                print('Max retries reached. Exiting current loop.')

        current_time = datetime.datetime.now()
        # 格式化當前時間為字符串
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        # 打印帶有當前時間的消息
        print('\n', '-' * long_sleep_time,
              f'本次main循環結束,0.5 秒後進入下一次循環,當前時間:{formatted_time}', '-' * 10,
              '\n\n')
        sleep(0.5)
