# FvgHost

from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime
import os.path
import sys
import pandas as pd
from Strategies.FVG.FvgStrategy import FvgStrategy
import backtrader as bt
from Charting import chart_utils as cu

class FvgHost(bt.Strategy):
    def log(self, txt, dt=None):
        ''' 用於記錄的函數'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0]  # 資料的收盤價
        self.data_history_index = 0  # 資料歷史索引
        self.fvg = FvgStrategy()  # FVG策略的實例
        self.count = 0  # 計數器
        self.ev_trades_count = {  # 正向和負向交易的計數
            'p_ev': 0,
            'n_ev': 0,
        }

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        if self.broker.orders:  # 如果有未完成的訂單，則取消它們
            [self.cancel[o] for o in self.broker.orders if o.status < 4]

        # 記錄交易的利潤
        self.log('OPERATION PROFIT, GROSS {0:8.2f}, NET {1:8.2f}'.format(
            trade.pnl, trade.pnlcomm))

        # 更新正向和負向交易計數
        if trade.pnl >= 0:
            self.ev_trades_count['p_ev'] += 1
        else:
            self.ev_trades_count['n_ev'] += 1

        # 記錄正向和負向交易計數
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
            else:  # 賣出
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

        if self.data_history_index > 60:  # 如果資料歷史索引大於60
            adjusted_size = 0.3 * self.broker.getcash() / self.dataclose.close[0]  # 計算調整後的交易量
            self.fvg_data_points = self.fvg.cycle_chunk(self.dataclose)  # 呼叫FVG策略的cycle_chunk方法
            long_entry = self.fvg.long()  # 呼叫FVG策略的long方法
            short_entry = self.fvg.short()  # 呼叫FVG策略的short方法

            # 如果沒有持倉且有長多倉信號，則建立買入訂單
            if not self.position and long_entry['acceptance']:
                take_profit_price = 1.01 * self.dataclose.close[0]
                stop_price = long_entry['fvg']['fvg_low']
                self.buy_bracket(size=adjusted_size, limitprice=take_profit_price, stopprice=stop_price, exectype=bt.Order.Market)

            # 如果沒有持倉且有短空倉信號，則建立賣出訂單
            if not self.position and short_entry['acceptance']:
                take_profit_price = 0.99 * self.dataclose.close[0]
                stop_price = short_entry['fvg']['fvg_high']
                self.sell_bracket(size=adjusted_size, limitprice=take_profit_price, stopprice=stop_price, exectype=bt.Order.Market)