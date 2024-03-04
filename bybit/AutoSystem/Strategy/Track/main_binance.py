# -*- coding: utf-8 -*-
import ccxt
import pandas as pd
import datetime
import threading
from time import sleep

long_sleep_time = 0.3
# 跟单倍数
follow_trading  = 1
# 创建OKEx交易所对象
proxy = ''
proxy = {'http': 'http://127.0.0.1:10100', 'https': '127.0.0.1:10100'}

# =交易所配置
okex_exchange = ccxt.okx({


    # 137 账户
    'apiKey': '',
    'secret': '',
    'password': '',
    'timeout': 3000,
    'rateLimit': 10,
    'proxies': proxy,
    'enableRateLimit': False})

# 创建 binance 交易所对象
b_exchange = ccxt.binance({
    'apiKey': 'SFBOyTcV4hGTG6NHjLQDsz5xClNXUEPlyjiBTmFuJE3ZmLWxXK3aWZBhqrF1xVt7',
    'secret': 'HWsJkHqYITA9Q9lVRX6g0GnOW5rcFWdTmiGLFrvm64htc1H2EucJmhifeLk8E6Yh',
    'timeout': 3000,
    'enableRateLimit': True,  # 启用请求限制
    'proxies': proxy,
})

# 封装交易所symbol格式
def get_okex_positions(symbol):
    inst_id = f"{symbol}-USDT-SWAP"
    return inst_id

# 封装交易所symbol格式
def get_binance_positions(symbol):
    inst_id = f"{symbol}USDT"
    return inst_id


# 币安 下单
def bg_close_position(symbol, side, quantity):
    try:
        response = b_exchange.fapiprivate_post_order({'symbol': get_binance_positions(symbol), 'quantity': quantity, 'side': side, 'type': 'MARKET'})
        print(response)
    except Exception as e:
        print(f"An error occurred placing the order: {e}")
        return None

# 辅助函数处理下单响应
def handle_order_response(order_response):
    if 'code' in order_response and order_response['code'] == '00000':
        print("下单成功！")
        # 在这里可以继续处理下单成功后的逻辑
    else:
        print("下单失败！")
        print("错误信息：", order_response.get('msg', '未提供错误信息'))
# 币种同步主函数
def main(ok_trades, b_trades, symbol, size):
    # 锁定线程，确保打印输出不会交织
    # with print_lock:

    total_open_deal_count_OK_long = 0
    total_open_deal_count_bg_long = 0
    total_open_deal_count_OK_short = 0
    total_open_deal_count_bg_short = 0
    # 获取OK跟单账户持仓信息,函数外面直接获取 ok API 是2s 10次 每个币种都抓不够用
    # 如果有数据就计算
    if ok_trades['data']:
        # 提取 instId 和 availPos 字段
        selected_OK_trades = [{'交易对': item['instId'],'方向': item['posSide'], 'ID': item['posId'], '持仓数量': item['pos']} for item in ok_trades['data']]

        # 创建DataFrame
        positions_OK = pd.DataFrame(selected_OK_trades)
        # ok交易所的币跟张数转换 重要 重要 重要
        positions_OK['持仓数量'] = positions_OK['持仓数量'].astype(float) * size

        # 计算OK的仓位数量
        # 过滤出当下 symbol 方向数据
        positions_OK = positions_OK[positions_OK['交易对'] == get_okex_positions(symbol)]
        # 过滤出long方向数据
        long_positions_OK = positions_OK[positions_OK['方向'] == 'long']
        # 统计long仓位总数
        total_open_deal_count_OK_long = long_positions_OK['持仓数量'].astype(float).sum()

        if total_open_deal_count_OK_long > 0:
            print(long_positions_OK)
            print(f"OK LONG {symbol}总持仓数量:", total_open_deal_count_OK_long)
        # 过滤出 short 方向数据
        short_positions_OK = positions_OK[positions_OK['方向'] == 'short']
        # 统计 short 仓位总数
        total_open_deal_count_OK_short = short_positions_OK['持仓数量'].astype(float).sum()
        if total_open_deal_count_OK_short > 0:
            print(short_positions_OK)
            print(f"OK short {symbol}总持仓数量:", total_open_deal_count_OK_short)
    else:
        print(f"OK {symbol}没有持仓")

    # 筛选 binance 当前币种数据
    b_position = None
    for position in b_trades:
        if position['symbol'] == get_binance_positions(symbol):
            b_position = position
            break

    # 如果 binance 账户 有持仓
    if b_position and float(b_position['positionAmt']) != 0:
        selected_trades = {'交易对': b_position['symbol'],  '开仓时间': b_position['updateTime'], '方向': '多头' if float(b_position['positionAmt']) > 0 else '空头', '持仓数量': b_position['positionAmt']}

        if float(selected_trades['持仓数量']) > 0:
            total_open_deal_count_bg_long += abs(float(selected_trades['持仓数量']))
        else:
            total_open_deal_count_bg_short += abs(float(selected_trades['持仓数量']))

        if total_open_deal_count_bg_long > 0:
            print('binance 多头总持仓数量:', total_open_deal_count_bg_long)

        if total_open_deal_count_bg_short > 0:
            print('binance 空头总持仓数量:', total_open_deal_count_bg_short)
    else:
        print(f"binance 没有 {symbol} 持仓")


    # 判断是否需要进行同步
    if ok_trades['code'] == '0' and b_position['symbol']:
        # 多头
        if total_open_deal_count_OK_long != total_open_deal_count_bg_long / follow_trading:  # 计算需要跟单倍数
            # 计算差值
            quantity_diff = total_open_deal_count_OK_long - total_open_deal_count_bg_long / follow_trading
            # print(quantity_diff)
            if quantity_diff > 0:
                # 需要加仓到 币安
                # 下单数量
                order_size = quantity_diff * follow_trading
                print(f"需要加仓到 币安：加仓数量为 {order_size}，同步倍数{follow_trading}")
                # 调用下单函数
                bg_close_position(symbol, 'BUY', order_size)
            else:
                # 需要减仓从 币安
                quantity_diff = abs(quantity_diff)
                order_size = quantity_diff * follow_trading
                print(f"需要减仓从 币安：减仓数量为 {order_size}")
                # 调用下单函数
                bg_close_position(symbol, 'SELL', order_size)
        else:
            print(f"OKEx 和 binance 的 long {symbol}持仓数量已经同步")

        # 空头
        if total_open_deal_count_OK_short != total_open_deal_count_bg_short/follow_trading: # 计算需要跟单倍数
            # 计算差值
            quantity_diff = total_open_deal_count_OK_short - total_open_deal_count_bg_short/follow_trading
            # print(quantity_diff)
            if quantity_diff > 0:
                # 需要开单 币安
                order_size = quantity_diff * follow_trading
                # 检查下单数量
                if order_size < size:
                    print(f"空头开单数量低于{size}，不开")
                print(f"正在binance 开short单：数量为 {order_size}，同步倍数{follow_trading}")
                # 调用下单函数
                bg_close_position(symbol, 'SELL', order_size)
            else:
                # 需要减仓 币安
                quantity_diff = abs(quantity_diff)
                order_size = quantity_diff * follow_trading
                print(f"正在 short 平仓{symbol}从 binance：平仓数量为 {order_size}")
                # 调用下单函数
                bg_close_position(symbol, 'BUY', order_size)
        else:
            print(f"OKEx 和 binance 的 short {symbol}持仓数量已经同步")

    else:
        print('api有获取失败行为，不做同步处理')
    # 本币种主体同步逻辑结束

    # 格式化当前时间为字符串
    formatted_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 打印带有当前时间的消息
    print('\n', '-' * 5, f'{symbol}同步结束，当前时间：{formatted_time}', '-' * 5, '\n\n')
    sleep(0)


if __name__ == '__main__':
    symbols = ['ETH', 'SOL', 'BTC']  # 要处理的币种列表
    symbol_min_size = {
        'BTC': 0.01,
        'ETH': 0.1,
        'SOL': 1,
        'XRP': 100,
        'LTC': 1,
        # 添加其他币种的最小下单数量
    }
    print_lock = threading.Lock() # 创建线程锁对象
    max_retries = 100  # 设置最大重试次数
    consecutive_failures  = 0  # 初始化当前重试次数
    while consecutive_failures < max_retries:
        try:
            # ok可以所有币种先爬出来
            ok_trades = okex_exchange.private_get_account_positions()
            b_trades = b_exchange.fapiprivatev2_get_positionrisk()
            threads = []  # 创建线程列表
            for symbol in symbols:
                size = symbol_min_size.get(symbol, 1)
                thread = threading.Thread(target=main, args=(ok_trades, b_trades, symbol, size))
                threads.append(thread)
                thread.start()
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            # 如果成功运行完所有币种，重置连续失败次数
            consecutive_failures = 0
        except Exception as e:
            consecutive_failures += 1
            print(f"Exception occurred: {e}")
            if consecutive_failures < max_retries:
                print(f"Retrying... (Retry {consecutive_failures} of {max_retries})")
                sleep(long_sleep_time)
            else:
                print("Max retries reached. Exiting current loop.")

        current_time = datetime.datetime.now()
        # 格式化当前时间为字符串
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        # 打印带有当前时间的消息
        print('\n', '-' * 10,
              f'本次main循环结束，{long_sleep_time} 秒后进入下一次循环，当前时间：{formatted_time}', '-' * 10,
              '\n\n')
        sleep(long_sleep_time)