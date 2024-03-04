import sys
import ccxt
from datetime import datetime

import os
try :

    bybit = ccxt.bybit({
        'apiKey': "vzu4CkrZcOg9sN25Kx",
        'secret': "6rhrjwgyimIAAW0I89fHaOOeQx6a87kem3hd"})
    
    line_key = "iQZtrIoPSXPie4ZcnlpPAaoVdZeQAAWL70qELFbpnmA"
    timestamp = float(bybit.publicGetV3PublicTime()['result']['timeSecond'])

    # 将时间戳转换为datetime对象
    dt = datetime.fromtimestamp(float(timestamp))

    # 获取日期和时间的字符串表示
    _date = dt.strftime('%Y-%m-%d')  # 格式化日期为 '年-月-日'
    _time = dt.strftime('%H:%M:%S')  # 格式化时间为 '时:分:秒'

    os.system('date {} && time {}'.format(_date, _time))

except BaseException as err:
    bybit.send_line_message(line_key, "【同步時間發生異常】"+ err)
    raise Exception("An error occured", err)    