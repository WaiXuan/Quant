import re
import tkinter as tk
import time
import os
import requests
import json
from ttkbootstrap import Style
from ttkbootstrap.constants import *
import ttkbootstrap as ttk
from datetime import datetime
import threading
import sys
import subprocess

from multiprocessing import Process
from tkinter.ttk import Notebook
from tkinter import messagebox

# 程式UI畫面設定
class UIset() :
    
    def __init__(self): 
        self.start = 0
        print('程式連線成功...')
    
    #策略下拉選單JSON LOAD
    def strategy_json_load(self) : 
        strategy_list = []
        f = open('Bybit\AutoSystem\Strategy.json',encoding="utf-8")
        data = json.load(f)  
        for strategy_name, strategy_data in data.items():
            strategy_list.append(strategy_data["strategy"] + " " + strategy_data["symbol"] )
        return strategy_list
    
    #策略下拉選單JSON LOAD
    def BybitAPI_json_load(self) : 
        strategy_list = []
        f = open('Bybit\AutoSystem\secret.json',encoding="utf-8")
        data = json.load(f)
        for strategy_name, strategy_data in data.items():
            if( strategy_name == "LINE_API") :
                continue 
            strategy_list.append(strategy_name)
        return strategy_list
        
    
    def set(self,login_window, open_type) :
        pd_y = 20 # pady Y 間格距離

        title_text = tk.Label(text = "自動化策略交易..v0", fg ="skyblue", bg="#323232")
        title_text.config(font ='微軟正黑體 20 bold')
        title_text.pack(pady=(0, pd_y))

        #策略下拉選單(text)
        strategy_text = tk.Label(text = "策略選擇", fg ="white", bg="#323232")
        strategy_text.config(font ='微軟正黑體 15 bold')
        strategy_text.pack(anchor='w')   #靠左對齊


        #策略下拉選單
        strategy_select = ttk.Combobox( values = self.strategy_json_load())
        strategy_select.current(0)
        strategy_select["width"] = 80
        strategy_select.pack(pady=(0, pd_y))

        #Bybit_API下拉選單(text)
        BybitAPI_text = tk.Label(text = "BybitAPI選擇", fg ="white", bg="#323232")
        BybitAPI_text.config(font ='微軟正黑體 15 bold')
        BybitAPI_text.pack(anchor='w')   #靠左對齊


        #Bybit_API
        BybitAPI_select = ttk.Combobox( values = self.BybitAPI_json_load())
        BybitAPI_select.current(0)
        BybitAPI_select["width"] = 80
        BybitAPI_select.pack(pady=(0, pd_y))


        Leverage_text = tk.Label(text = "槓桿倍率", fg ="white", bg="#323232")
        Leverage_text.pack(anchor='w')

        Leverage__input = tk.Entry()
        Leverage__input["width"] = 80
        Leverage__input.pack(pady=(0, 5))




#無金鑰版 登入窗口
class Without_password_check() :

    def __init__(self): 
        login_window = tk.Tk()
        style1 = Style(theme="darkly")
        login_window = style1.master

        login_window.title('TIXBOT')
        
        width = login_window.winfo_screenwidth() *.18
        height = login_window.winfo_screenheight() *.52
        login_window.geometry("%dx%d" % (width, height))

        login_window.config() # bg="#323232"
        login = UIset()
        login.set(login_window,'2')

        login_window.mainloop()



if __name__ == '__main__':

    Without_password_check()   #免金鑰