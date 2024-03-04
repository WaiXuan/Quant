import backtrader as bt
import talib
import backtrader.analyzers as btanalyzers
import time
from datetime import datetime
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc
import pandas as pd
import matplotlib.dates as mpl_dates
import matplotlib.patches as mpatches
import datetime as dt
from matplotlib.patches import Rectangle


# 定義文件名、符號和策略名稱
filename = "BTCUSDT_15m_2023-4-2023-10_Monthly"
symbol = filename[:7]
strategy_name = "Bollinger"


def pct_delta(a, b):
    return (abs(a - b) / b) * 100

def chart_fvg(fvg_data_points, x_current):
    plt.style.use('ggplot')
    context = mpl_dates.date2num(x_current)

    # Extracting Data for plotting

    pathfile = "C:\Data\Git\Quantitative\BackTrader\Input\\" + filename + ".csv"
    data = pd.read_csv(pathfile).head(14445)
    ohlc = data.loc[:, ['Datetime', 'Open', 'High', 'Low', 'Close']]
    ohlc['Datetime'] = pd.to_datetime(ohlc['Datetime'])
    ohlc['Datetime'] = ohlc['Datetime'].apply(mpl_dates.date2num)
    ohlc = ohlc.astype(float)
    ohlc = ohlc.astype(float)

    # Creating Subplots
    fig, ax = plt.subplots()

    candlestick_ohlc(ax, ohlc.values, width=0.01, colorup='green', colordown='red', alpha=0.8)

    # Setting labels & titles
    ax.set_xlabel('Datetime')
    ax.set_ylabel('Price')
    fig.suptitle('btc-binance')

    # Formatting Date
    date_format = mpl_dates.DateFormatter('%Y-%m-%d %H:%M:%S')
    ax.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()

    fig.tight_layout()

    for dp in fvg_data_points['delta_p']:
        #if not dp['fvg_invalidated']:
            start = mpl_dates.date2num(dp['fvg_timestamp'])
            date_delta = context-start
            fvg_delta = dp['fvg_high'] - dp['fvg_low']
            ax.add_patch(Rectangle((start, dp['fvg_low']), date_delta, fvg_delta, color='green', alpha=0.5))

    for dp in fvg_data_points['delta_n']:
        #if not dp['fvg_invalidated']:
            start = mpl_dates.date2num(dp['fvg_timestamp'])
            date_delta = context - start
            fvg_delta = dp['fvg_high'] - dp['fvg_low']
            ax.add_patch(Rectangle((start, dp['fvg_low']), date_delta, fvg_delta, color='red', alpha=0.5))

    plt.show()





# 定義 FvgStrategy 類別
class FvgStrategy():

    # FVG_DELTA_THRESHOLD 用於定義擺盪區域的閾值
    FVG_DELTA_THRESHOLD = 1.5

    def __init__(self):
        # 初始化 FVG 策略
        self.fvg_tracker = {
            'delta_p': [],
            'delta_n': [],
        }

    def cycle_chunk(self, chunk):
        #self.reset_fvg_tracker()
        self.chunk = chunk
        for i in range(-60, 1, 1):
            try:
                # 逐個時間段進行分析，取得擺盪區域的信息
                self.get_movement_delta(chunk, i)
            except Exception as e:
                pass

        #self.remove_invalidated_fvg_zones()

        return self.fvg_tracker

    def reset_fvg_tracker(self):
        # 重置 FVG 跟蹤器
        self.fvg_tracker = {
            'delta_p': [],
            'delta_n': [],
        }

    def remove_invalidated_fvg_zones(self):
        # 移除無效的 FVG 區域
        for idx, x in enumerate(self.fvg_tracker['delta_p']):
            self.fvg_tracker['delta_p'][idx]['fvg_invalidated'] = False
            for i in range(x['fvg_chunk_index'], 1, 1):
                if self.chunk.close[i] < x['fvg_low']:
                    # 標記為無效
                    self.fvg_tracker['delta_p'][idx]['fvg_invalidated'] = True
                    break

        for idx, x in enumerate(self.fvg_tracker['delta_n']):
            self.fvg_tracker['delta_n'][idx]['fvg_invalidated'] = False
            for i in range(x['fvg_chunk_index'], 1, 1):
                if self.chunk.close[i] > x['fvg_high']:
                    # 標記為無效
                    self.fvg_tracker['delta_n'][idx]['fvg_invalidated'] = True
                    break

    def get_movement_delta(self, chunk, index) -> int:
        # 判斷是否為牛市 FVG
        if chunk.high[index] < chunk.low[index + 2] and chunk.high[index] > chunk.open[index + 1] and chunk.low[index + 2] < chunk.close[index + 1]:
            if pct_delta(chunk.high[index], chunk.low[index + 2]) >= self.FVG_DELTA_THRESHOLD:
                self.fvg_tracker['delta_p'].append({
                    'fvg_high': chunk.low[index + 2],
                    'fvg_low': chunk.high[index],
                    'fvg_timestamp': chunk.datetime.datetime(index),
                    'fvg_chunk_index': index + 2
                })
                print(self.fvg_tracker)                
            else :
                print(pct_delta(chunk.high[index], chunk.low[index + 2]))
        # 判斷是否為熊市 FVG
        if chunk.low[index] > chunk.high[index + 2] and chunk.low[index] < chunk.open[index + 1] and chunk.high[index + 2] > chunk.close[index + 1]:
            if pct_delta(chunk.high[index + 2], chunk.low[index]) >= self.FVG_DELTA_THRESHOLD:
                self.fvg_tracker['delta_n'].append({
                    'fvg_high': chunk.low[index],
                    'fvg_low': chunk.high[index + 2],
                    'fvg_timestamp': chunk.datetime.datetime(index),
                    'fvg_chunk_index': index + 2
                })
                print('-----')
                print( chunk.low[index])
                print(self.fvg_tracker)
            else :
                print(pct_delta(chunk.high[index], chunk.low[index + 2]))
    def nearest_delta_n_fvg(self):
        nearest_p_fvg = None
        nearest_p_fvg_distance = 99999
        for x in self.fvg_tracker['delta_n']:
            if not x['fvg_invalidated'] and (x['fvg_low'] - self.chunk.close[0]) < nearest_p_fvg_distance:
                nearest_p_fvg = x

        return nearest_p_fvg

    def nearest_delta_p_fvg(self):
        nearest_n_fvg = None
        nearest_n_fvg_distance = 99999
        for x in self.fvg_tracker['delta_p']:
            if not x['fvg_invalidated'] and (self.chunk.close[0] - x['fvg_low']) < nearest_n_fvg_distance:
                nearest_n_fvg = x

        return nearest_n_fvg

    def short(self):
        # 判斷是否可以進行做空交易
        fvg = self.nearest_delta_n_fvg()
        acceptance = False

        if fvg is not None and self.chunk.close[0] < fvg['fvg_low']:
            if fvg['fvg_low'] < self.chunk.open[-1] and fvg['fvg_low'] < self.chunk.close[-1]:
                acceptance = True

        return {
            'fvg': fvg,
            'acceptance': acceptance
        }

    def long(self):
        # 判斷是否可以進行做多交易
        fvg = self.nearest_delta_p_fvg()
        acceptance = False

        if fvg is not None and self.chunk.close[0] > fvg['fvg_high']:
            if fvg['fvg_high'] > self.chunk.open[-1] and fvg['fvg_high'] > self.chunk.close[-1]:
                acceptance = True

        return {
            'fvg': fvg,
            'acceptance': acceptance
        }

# 定義 FvgHost 類別
class FvgHost(bt.Strategy):

    def log(self, txt, dt=None):
        ''' 用於日誌輸出的函數'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.data
        self.data_history_index = 0
        self.fvg = FvgStrategy()
        self.count = 0
        self.ev_trades_count = {
            'p_ev': 0,
            'n_ev': 0,
        }

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        if self.broker.orders:
            [self.cancel[o] for o in self.broker.orders if o.status < 4]

        self.log('OPERATION PROFIT, GROSS {0:8.2f}, NET {1:8.2f}'.format(
            trade.pnl, trade.pnlcomm))

        if trade.pnl >= 0:
            self.ev_trades_count['p_ev'] += 1
        else:
            self.ev_trades_count['n_ev'] += 1

        self.log('Trade tally, +EV: {}, -EV: {}'.format(self.ev_trades_count['p_ev'], self.ev_trades_count['n_ev']))

    def notify_order(self, order):
            if order.status in [order.Submitted, order.Accepted]:
                return

            if order.status in [order.Completed]:
                if order.isbuy():
                    self.log(
                        'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                        (order.executed.price,
                         order.executed.value,
                         order.executed.comm))
                else:  # Sell
                    self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                             (order.executed.price,
                              order.executed.value,
                              order.executed.comm))
            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                self.log('Order Canceled/Margin/Rejected')

    def next(self):
        self.count += 1
        try:
            self.data_history_index += 1
        except Exception as e:
            pass

        if self.data_history_index > 60:
            adjusted_size = 0.3 * self.broker.getcash() / self.dataclose.close[0]
            # print(self.dataclose.close[0])
            self.fvg_data_points = self.fvg.cycle_chunk(self.data)
            # long_entry = self.fvg.long()
            # short_entry = self.fvg.short()

            # if not self.position and long_entry['acceptance']:
            #     take_profit_price = 1.01 * self.dataclose.close[0]
            #     stop_price = long_entry['fvg']['fvg_low']
            #     self.buy_bracket(size=adjusted_size, limitprice=take_profit_price, stopprice=stop_price, exectype=bt.Order.Market)

            # if not self.position and short_entry['acceptance']:
            #     take_profit_price = 0.99 * self.dataclose.close[0]
            #     stop_price = short_entry['fvg']['fvg_high']
            #     self.sell_bracket(size=adjusted_size, limitprice=take_profit_price, stopprice=stop_price, exectype=bt.Order.Market)

            if self.count == 13445:
                print(self.fvg_data_points)
                chart_fvg(self.fvg_data_points, self.dataclose.datetime.datetime(0))
                exit()

# 主程式進入點
if __name__ == "__main__":
    # 創建 Cerebro 實體
    cerebro = bt.Cerebro()

    # 添加數據源
    pathfile = "C:\Data\Git\Quantitative\BackTrader\Input\\" + filename + ".csv"
    df = pd.DataFrame(
        pd.read_csv(pathfile, delimiter=",", index_col="Datetime", parse_dates=True)
    )
    df.index = pd.to_datetime(df.index, format="mixed", utc=True)
    brf_min_bar = bt.feeds.PandasData(
        dataname=df,
        timeframe=bt.TimeFrame.Minutes,
    )
    cerebro.adddata(brf_min_bar)

    # 設置初始資本和手續費
    cerebro.broker.setcash(1000000)
    cerebro.broker.set_shortcash(False)
    cerebro.broker.setcommission(commission=0.0015, margin=None, mult=10)

    # 添加策略
    cerebro.addstrategy(FvgHost)

    # 添加分析器
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(btanalyzers.Returns, _name='returns')

    # 執行策略
    print("Starting Portfolio Value: {}".format(cerebro.broker.getvalue()))
    results = cerebro.run()
    print("End Portfolio Value: {}".format(cerebro.broker.getvalue()))

    # 提取分析結果
    ratio_list = [[
        x.analyzers.returns.get_analysis()['rtot'],
        x.analyzers.returns.get_analysis()['rnorm100'],
        x.analyzers.drawdown.get_analysis()['max']['drawdown'],
        x.analyzers.sharpe.get_analysis()['sharperatio']] for x in results]

    ratio_df = pd.DataFrame(ratio_list, columns=['Total_return', 'APR', 'DrawDown', 'Sharpe_Ratio'])
    print(ratio_df)

    # 繪製圖表
    cerebro.plot(style="candle")

    print("ending")
