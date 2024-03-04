import sys
sys.path.append("C:/Data/Git/Quantitative/bybit/AutoSystem/main")
from PerpBybit import PerpBybit
from datetime import datetime
import pandas as pd

def format_time(ms_time):
    sec_time = int(ms_time) / 1000  # Convert milliseconds to seconds
    datetime_time = datetime.fromtimestamp(sec_time)
    formatted_time = datetime_time.strftime("%Y/%m/%d %H:%M")
    return formatted_time

bybit = PerpBybit(
    apiKey="DBFGTTUAABNSXPDYSS",
    secret="YEXXLVEKELCWYPWPLINEVDUROLPANELCLTQP",
)
data = bybit.position= bybit.get_close_pnl('ETHUSDT')
list_data = data['result']['list']
    
columns_to_extract = [
                        "symbol",           # 合約名稱
                        "orderType",
                        "side",             # 買賣方向
                        "leverage",         # 持倉槓桿
                        "createdTime",
                        "updatedTime",
                        "avgEntryPrice",    # 平均入場價格
                        "avgExitPrice",     # 平均出場價格
                        #"orderId",
                        "closedPnl",        # 被平倉位的盈虧
                        "qty",              # 訂單數量
                        "cumEntryValue",    # 被平倉位的累計出場價值
                        "orderPrice",       # 訂單價格
                        "closedSize",       # 平倉數量
                        "execType",         # 執行類型
                        "fillCount",        # 成交筆數
                        "cumExitValue",     # 被平倉位的累計出場價值
                    ]

list_data = data['result']['list']
filtered_data = [
    {
        col: format_time(entry[col]) if col in ["createdTime", "updatedTime"] else entry[col]
        for col in columns_to_extract
    }
    for entry in list_data
]



# Convert the filtered data into a DataFrame
df = pd.DataFrame(filtered_data)


df.to_csv("C:\Data\Git\Quantitative\\bybit\AutoSystem\Output\交易紀錄.csv", index=False, encoding='gbk')

