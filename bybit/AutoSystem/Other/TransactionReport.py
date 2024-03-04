from PerpBybit import PerpBybit
from datetime import datetime
import pandas as pd


bybit = PerpBybit(
    apiKey="DBFGTTUAABNSXPDYSS",
    secret="YEXXLVEKELCWYPWPLINEVDUROLPANELCLTQP",
)
data = bybit.position= bybit.get_close_pnl('ETHUSDT', None, None) 
list_data = data['result']['list']
    
columns_to_extract = ['symbol',
                    'side', 
                    'funding',
                    'orderLinkId',
                    'orderId',
                    'fee']

list_data = data['result']['list']
filtered_data = [{col: entry[col] for col in columns_to_extract} for entry in list_data]

# Convert the filtered data into a DataFrame
df = pd.DataFrame(filtered_data)
