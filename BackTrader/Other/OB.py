# //@version=4
# study("Order Block Finder", overlay = True)
tip1 = "此指標有助於識別機構性的訂單區塊（OB）。OB通常預示著強勢行情的開始。有很高的機會OB價位將來會再次到達，這些價位是放置限價訂單的有趣選擇。牛市OB是連續的上漲蠟燭之前的最後一根下跌蠟燭。熊市OB是連續的下跌蠟燭之前的最後一根上漲蠟燭。"
tip2 = "!實驗性功能!\n從不同時間框架中查找訂單區塊。價格通道是準確的，但箭頭位置不準確。在選擇高於圖表的時間框架時最有用。"
tip3 = "識別訂單區塊所需的連續蠟燭數"
tip4 = "從潛在OB的收盤價到連續蠟燭的第一根的收盤價之間的絕對百分比變動"
colors = input("LIGHT", "顏色主題", options=["DARK", "LIGHT"])
periods = input(7, "識別OB的相關期數", tooltip=tip3)
threshold = input(0.0, "有效OB的最低百分比變動", step=0.1, tooltip=tip4)
bull_channels = input(2, "顯示多頭通道數")
bear_channels = input(2, "顯示空頭通道數")

copen, chigh, clow, cclose = request.security("BINANCE:BTCUSDT", "30T", ohlc4)

ob_period = periods + 1
absmove = ((abs(cclose[ob_period] - cclose[1])) / cclose[ob_period]) * 100
relmove = absmove >= threshold

bullcolor = color.white if colors == "DARK" else color.green
bearcolor = color.blue if colors == "DARK" else color.red

bullishOB = cclose[ob_period] < copen[ob_period]

upcandles = 0
for i in range(1, periods):
    if cclose[i] > copen[i]:
        upcandles += 1

OB_bull = bullishOB and (upcandles == periods) and relmove
OB_bull_chigh = chigh[ob_period] if OB_bull else None
OB_bull_clow = clow[ob_period] if OB_bull else None
OB_bull_avg = (OB_bull_chigh + OB_bull_clow) / 2 if OB_bull else None

bearishOB = cclose[ob_period] > copen[ob_period]

downcandles = 0
for i in range(1, periods):
    if cclose[i] < copen[i]:
        downcandles += 1

OB_bear = bearishOB and (downcandles == periods) and relmove
OB_bear_chigh = chigh[ob_period] if OB_bear else None
OB_bear_clow = clow[ob_period] if OB_bear else None
OB_bear_avg = (OB_bear_chigh + OB_bear_clow) / 2 if OB_bear else None

plotshape(OB_bull, title="Bullish OB", style=shape.triangleup, color=bullcolor, textcolor=bullcolor, size=size.tiny, location=location.belowbar, text="Bull")
plotshape(OB_bear, title="Bearish OB", style=shape.triangledown, color=bearcolor, textcolor=bearcolor, size=size.tiny, location=location.abovebar, text="Bear")

alertcondition(OB_bull, title='New Bullish OB detected', message='New Bullish OB detected - This is NOT a BUY signal!')
alertcondition(OB_bear, title='New Bearish OB detected', message='New Bearish OB detected - This is NOT a SELL signal!')