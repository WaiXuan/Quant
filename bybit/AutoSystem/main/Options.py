from PerpBybit import PerpBybit
from datetime import datetime, timedelta
from DBHelper import DBHelper
import time
import pandas as pd

class Options():         

# region 取得資訊
    # TODO 獲取指定 Delta IV Theta Gamma Vega
    # 獲取指定IV
    def get_iv_market_tickers(self, bybit, category, symbol, limit, expDate, iv) :
        data = pd.DataFrame(bybit.get_market_tickers(self, bybit, category, symbol, limit, expDate))
        result = data.iloc[(data['IV'] - iv).abs().argsort()[:1]]
        return result 
# endregion

# region 計算
    # 計算期權到期日
    def calculate_expDate(expDate):
        current_date = datetime.now()               # 獲取當前日期    
        exp_delta = timedelta(days=expDate)         # 將到期日轉換為 timedelta 對象    
        expiration_date = current_date + exp_delta  # 計算到期時間
        formatted_expiration_date = expiration_date.strftime('%d%b%y').upper() # 將到期時間轉換為指定格式        
        return formatted_expiration_date
# endregion

# region 期權策略

    # TODO 跨式期權 同時買入相同數量的看漲期權和看跌期權 行使價相同，到期日相同

    # TODO 備兌看漲 買入一份低行使價格的看漲期權（更接近當前市價）並賣出一份高行使價格的看漲期權

    # TODO 
    # TODO 跨式期權 同時買入相同數量的看漲期權和看跌期權 行使價相同，到期日相同

# endregion