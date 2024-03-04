# DB List 
資料表
LOG


```
'Strategy': strategy_name,
'開倉價格': self.pricein,
'平倉價格': self.priceout,
'原止損價格': min(sublist[1] for sublist in self.stoploss_data),
'開倉方向': '多',
'開倉時間': self.datein,
'關倉時間': self.dateout,                                        
'倉位總數量': self.allsize,
'倉位總金額': self.pricein * self.allsize,
'平倉數量': size,
'剩餘倉位': self.getposition().size - size,
'平倉原因': reason,
'實際收益': income,
'收益率': pcntchange,
'帳戶總金額': self.broker.getvalue(),
```




# 數據表


Record.Vegas
Symbol
strategy
timeframe
open
high
low
close
ema12
ema144
ema169
ema576
ema676
adosc
rsi
obv
volume_oscillator
KDJ K
KDJ D
KDJ J


#交易紀錄表

Trade.Vegas

Symbol
TimeFrame
AccountName
OrderId
Side
Size
Price
TotalValue
Reason
Action
OrderCase
ProfitPercent
ProfitSizePercent
CreateDT





Symbol	 symbol,
Strategy strategy_name,
開倉價格 pricein,
平倉價格 priceout,
原止損價格': max(sublist[0] for sublist in self.stoploss_data),
開倉放向: side
開倉時間: datein
關倉時間: dateout 
倉位總數量': size                                                                         
倉位總金額': pricein * size   
平倉數量': size * (-1),   
剩餘倉位': self.getposition().size - size,
平倉原因': reason,                                                                                                                 
實際收益': income,
收益率': pcntchange,
帳戶總金額': self.broker.getvalue(),
     



OrderCase
Symbol

帳號 account_name
USD 餘額 usd_balance
止盈趴數 stop_profit_percent                                                                                                                                                                                                                    
止盈倉位趴數 self.profit_size_percent                                        
止損趴數  stop_loss_percent                     
槓桿倍數  isLeverage

