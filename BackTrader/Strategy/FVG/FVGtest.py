
def pct_delta(a, b):
    return (abs(a - b) / b) * 100


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

    def get_movement_delta(self, chunk, index):
        # 判斷是否為牛市 FVG
        if chunk.high[index] < chunk.low[index + 2] and chunk.high[index] > chunk.open[index + 1] and chunk.low[index + 2] < chunk.close[index + 1]:
            if pct_delta(chunk.high[index], chunk.low[index + 2]) >= self.FVG_DELTA_THRESHOLD:
                self.fvg_tracker['delta_p'].append({
                    'fvg_high': chunk.low[index + 2],
                    'fvg_low': chunk.high[index],
                    'fvg_timestamp': chunk.datetime[index],
                    'fvg_chunk_index': index + 2
                })
        # 判斷是否為熊市 FVG
        if chunk.low[index] > chunk.high[index + 2] and chunk.low[index] < chunk.open[index + 1] and chunk.high[index + 2] > chunk.close[index + 1]:
            if pct_delta(chunk.high[index + 2], chunk.low[index]) >= self.FVG_DELTA_THRESHOLD:
                print(chunk)
                self.fvg_tracker['delta_n'].append({
                    'fvg_high': chunk.low[index],
                    'fvg_low': chunk.high[index + 2],
                    'fvg_timestamp': chunk.datetime[index],
                    'fvg_chunk_index': index + 2
                })

        return self.fvg_tracker
    
# 導入必要的庫
import pandas as pd  # 用於數據框操作
import pandas_ta as ta  # 用於技術分析指標
import numpy as np  # 用於數學運算
import plotly.graph_objects as go  # 用於繪製圖表
from scipy import stats  # 用於統計分析

# 從CSV文件中讀取比特幣價格數據
filename = "BTCUSDT_15m_2023-4-2023-10_Monthly"
pathfile = "C:\Data\Git\Quantitative\BackTrader\Strategy\FVG\\" + filename + ".csv"
df = pd.DataFrame(
    pd.read_csv(pathfile, delimiter=",", parse_dates=True)
)

# # 過濾掉交易量（volume）為0的數據行
# df = df[df['volume'] != 0]

# df.tail()

# 選擇前5000行數據進行進一步分析
df = df[0:5000]

fvg = FvgStrategy()
for i in range(1, len(df)):
    print(i)
    if i > 3 and i < 4950:
        fvg.fvg_tracker = fvg.get_movement_delta(df ,i)
    
    #Datetime,Open,High,Low,Close,Volume
print(fvg.fvg_tracker)
