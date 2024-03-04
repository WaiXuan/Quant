import datetime
import os
import requests 
import pandas as pd 
from zipfile import ZipFile

def download_spot_klines(symbol, period, start_date, end_date):
    data = pd.DataFrame()
    filename = '%s_%s_%s-%s-%s-%s_Monthly.csv' % (symbol, period, start_date.year, start_date.month, end_date.year, end_date.month)
    while start_date < end_date:
        date_year = start_date.year
        date_month = start_date.month
        if date_month < 10:
            date_month = '0%s' % date_month
        url = 'https://data.binance.vision/data/futures/um/monthly/klines/%s/%s/%s-%s-%s-%s.zip'%(
        symbol, period, symbol, period, date_year, date_month)
        # url = 'https://data.binance.vision/data/spot/monthly/klines/%s/%s/%s-%s-%s-%s.zip'%(
        # symbol, period, symbol, period, date_year, date_month)        
        
        r = requests.get (url)
        if r:
            with open ("%s-%s-%s-%s.zip" % (symbol, period, date_year, date_month), "wb") as code:
                code.write(r.content)
                print (url,'已经下载完毕')
        data = pd.concat([data, read_history_file(url)])
        start_date += pd.DateOffset(months=1)
    data.to_csv("C:\Data\Git\Quantitative\BackTrader\Input\\" +filename, index= False, encoding= 'gbk')

    print (filename,'CSV產生完成')
def read_history_file (url):
    zip_file = '%s.zip' % url.split('/')[-1].split('.')[0]
    csv_file = '%s.csv' % url.split('/')[-1].split('.')[0]
    try:
        # 解压缩，读取数据，生成想要的格式
        data = read_zpfile(zip_file, csv_file)
        data.columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume',
                      'header7','header7','header7','header7','header7','header7']
        # 转换时间
        data['Datetime']=pd.to_datetime (data['Datetime'], unit='ms') #UTC e时区的時間，格林威治的時間。
        data['Datetime']=data['Datetime']+pd.Timedelta (hours=8)
        #只保罶我们想要的列
        data = data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
        # 删除zip文件
        os.remove ("%s" % zip_file)
        # os.remove ("%s" % csv_file)
    except Exception as e:
        print(e)
    return data

def read_zpfile (zip_file, csv_file):
    zf = ZipFile(zip_file)
    file = zf.open(csv_file)
    df = pd.read_csv(file, encoding="'gbk")
    file.close ()
    zf.close ()
    return df

if __name__ =='__main__':
    print('開始執行')
    symbol = 'BTCUSDT'
    period = '15m'
    # 設定起始日期和結束日期
    start_date = datetime.datetime(2023, 4, 1)
    end_date = datetime.datetime(2023, 10, 1)
    download_spot_klines (symbol, period, start_date, end_date)