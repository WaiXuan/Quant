import backtrader as bt
from datetime import datetime
import pandas as pd


class MyStrategy(bt.Strategy):
    params = (
         ('RSI6period', 6),
         ('RSI24period', 24),
    )

    def log(self, txt, dt=None):
        # 日志函数
        dt = dt or self.datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))
        
    def __init__(self):
        self.dataclose=self.datas[0].close
        self.dataopen=self.datas[0].open
        self.datalow=self.datas[0].low
        self.datahigh=self.datas[0].high
        self.RSI6 = bt.indicators.RSI(self.data, period=self.p.RSI6period)
        self.RSI24 = bt.indicators.RSI(self.data, period=self.p.RSI24period)
        self.crossover = bt.ind.CrossOver(self.RSI6, self.RSI24) 
        self.order = None
        self.pricein = None     # 开仓价格
        self.datein = None      # 开仓日期
        self.priceout = None    # 平仓价格(每个bar结束的收盘价)
        self.dateout = None     # 平仓日期(每个bar结束的日期)
        self.content_list = []
        
    def next(self):
        data = self.datas[0]
        size = self.getposition(data).size
        if size == 0:
            if self.crossover > 0: 
                self.order = self.buy(size=200)
                # 获取买入成交价
                try:
                    self.pricein = data.open[1]
                    self.datein = bt.num2date(data.datetime[1])
                except:
                    self.pricein = data.close[0]
                    self.datein = bt.num2date(data.datetime[0])
            elif self.RSI6[0] < 30: 
                self.order = self.buy(size=200)
                # 获取买入成交价
                try:
                    self.pricein = data.open[1]
                    self.datein = bt.num2date(data.datetime[1])
                except:
                    self.pricein = data.close[0]
                    self.datein = bt.num2date(data.datetime[0])
        else:
            if self.crossover < 0:
                self.order = self.close(size=200)
            elif self.RSI6[0] > 80:
                self.order = self.close(size=200)

        pricein = self.data.open[0]
        # 如果size=0就是没有持仓
        if size > 0:
            # 持有多头
            self.priceout = self.data.close[0]
            self.dateout = bt.num2date(self.datas[0].datetime[0])
            basepoint = self.priceout / self.pricein*100
            pcntchange = (self.priceout-self.pricein)/self.pricein
            lowest_in_trade = self.data.low[0]
            lp = (lowest_in_trade - pricein) / pricein
            mae = lp
            fee = size*self.pricein*0.0016
            self.content_list.append({'price_open': self.pricein,
                                'price_close': self.priceout,
                                'datein': self.datein,
                                'dateout': self.dateout,
                                'symbol': 'SH.603998',
                                'return_margin': round(pcntchange, 2),
                                'margin_ratio': 10000,
                                'product': 'SH.603998',
                                'trade_side': size,
                                'return': round(pcntchange, 2),
                                'price_tick': 100,
                                'multiplier': 100,
                                'basepoint': basepoint,
                                'fee': fee,
                                'isblock': 0,
                                'strategy_name': 'RSI',
                                'params': '18_41',
                                'return_worst': round(mae, 2),
                                'return_worst_margin': round(mae, 2),
                                'volume': 200})


    def notify_order(self, order):

        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Rejected:
            self.log(f"Rejected : order_ref:{order.ref}  data_name:{order.p.data._name}")

        if order.status == order.Margin:
            self.log(f"Margin : order_ref:{order.ref}  data_name:{order.p.data._name}")

        if order.status == order.Cancelled:
            self.log(f"Concelled : order_ref:{order.ref}  data_name:{order.p.data._name}")

        if order.status == order.Partial:
            self.log(f"Partial : order_ref:{order.ref}  data_name:{order.p.data._name}")

        if order.status == order.Completed:
            if order.isbuy():
                self.log(f" BUY : data_name:{order.p.data._name} price : {order.executed.price} , cost : {order.executed.value} , commission : {order.executed.comm}")

            else:  # Sell
                self.log(f" SELL : data_name:{order.p.data._name} price : {order.executed.price} , cost : {order.executed.value} , commission : {order.executed.comm}")

    def notify_trade(self, trade):
        # 一个trade结束的时候输出信息
        if trade.isclosed:
            self.log('closed symbol is : {} , total_profit : {} , net_profit : {}' .format(
                            trade.getdataname(),trade.pnl, trade.pnlcomm))
            # self.trade_list.append([self.datas[0].datetime.date(0),trade.getdataname(),trade.pnl,trade.pnlcomm])

        if trade.isopen:
            self.log('open symbol is : {} , price : {} ' .format(
                            trade.getdataname(), trade.price))

    def stop(self):
        df = pd.DataFrame(self.content_list)
        df.to_csv("./指定输出内容.csv")


def run_strategy():
    # 初始化
    cerebro = bt.Cerebro()

    sh603998 = pd.read_excel(r'./SH.603998.xlsx')
    df = sh603998.loc[:, ['date', 'open_fq', 'high_fq', 'low_fq', 'close_fq', 'volume', 'open_interest']]
    df.index = pd.to_datetime(df['date'].astype(str))
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'open_interest']
    fromdate = datetime(2018, 5, 2)
    todate = datetime(2023, 3, 20)
    data = bt.feeds.PandasData(dataname=df, fromdate=fromdate, todate=todate)

    codename = 'sh603998'
    cerebro.adddata(data, name=codename)
    cerebro.addstrategy(MyStrategy)
    startcash = 100000000
    cerebro.broker.setcash(startcash)

    result = cerebro.run()


if __name__ == "__main__":
    run_strategy()