#import DBHelper
from PerpBybit import PerpBybit
from datetime import datetime
from DBHelper import DBHelper
import time

class Common():         
    # TODO
    # 開單紀錄
    # 帳號、時間、Symbol、Side、價格、數量、總價值、OrderId、Reason

    def open_order(self, bybit, side, market_price, sendMessage, reason, trigger_price = None):
        try :    
            usd_balance = float(bybit.get_wallet_balance("USDT"))
            quantity_in_usd = usd_balance * 0.99 * self.isLeverage
            long_quantity = float(bybit.convert_amount_to_precision(self.pair, float(
                bybit.convert_amount_to_precision(self.pair, quantity_in_usd / market_price)
            )))
            if trigger_price == None :
                trigger_price = round(float(market_price * (1-self.stop_loss_percent)), 2) if side == 'Buy' else round(float(market_price * (1+self.stop_loss_percent)), 2)
            bybit.place_linear_market_stop_loss(self.pair, side, "Market", long_quantity, None, trigger_price, self.isLeverage)
            position= bybit.get_position(self.pair)                                
            message = (
                f'\n【{self.symbol} 做'+ ('多' if side == 'Buy' else '空') + '市價單】'
                f'\n帳號:{self.account_name}'
                f'\n時間:{datetime.now().strftime("%Y/%m/%d %H:%M:%S")}'                                        
                f'\n原帳戶餘額:{usd_balance}'
                f'\n價格:{position["avgPrice"]}$'
                f'\n數量:{float(position["size"])}'
                f'\n價值:{round(float(position["positionValue"]), 2)}$'
                f'\n開倉原因:{reason}'
            )
            self.stop_profit = float(position["avgPrice"]) * ((1 + self.stop_profit_percent) if side == 'Buy' else (1 - self.stop_profit_percent))
            
            # 將資訊存入DB
            # param_dict={
            #     'Symbol' : self.pair,
			# 	'AccountName': self.account_name,
			# 	'TimeFrame': self.timeframe,
			# 	'OrderId': None,
			# 	'Side': side,
			# 	'Price': float(position["avgPrice"]),
			# 	'TotalValue':float(round(position["positionValue"]), 2),
			# 	'Reason':reason,
			# 	'Action': '開倉',
			# 	'OrderCase': int(self.ordercase),
            #     'ProfitPrice': round(self.stop_profit, 2),
			# 	'ProfitPercent': self.stop_profit_percent,
			# 	'ProfitSizePercent': float(round(self.profit_size_percent, 2)),
            #     'LossPrice': float(round(trigger_price, 2)),
			# 	'LossPercent': round(self.stop_loss_percent, 2),
			# 	'IsLeveRage': self.isLeverage
            # }
            # db = DBHelper()
            # db.execute_sp('Trade.usp_InsertVeags', param_dict)                
            
            if sendMessage :
                print(message)                                
                bybit.send_line_message(self.line_key, message)
                
        except Exception as err:
            raise Exception(err)

    # TODO
    # 開單紀錄
    # 帳號、時間、Symbol、Side、價格、數量、總價值、OrderId、Reason、盈虧，倉位餘額

    def close_order(self, bybit, side, market_price, close_percent, sendMessage, reason):
        try :
            position= bybit.get_position(self.pair)                 
            quantity = float(
                bybit.convert_amount_to_precision(self.pair, float(position["size"]) * close_percent)
            )
            exchange_quantity = quantity * market_price
            bybit.place_linear_market_stop_loss(self.pair, side, "Market", quantity, None, None, self.isLeverage)   
            position= bybit.get_position(self.pair)           
            if sendMessage :                                                                                           
                message = (
                    f'\n【{self.symbol}平'+ ('空' if side == 'Buy' else '多')+'市價單】'
                    f'\n帳號:{self.account_name}'                
                    f'\n時間:{datetime.now().strftime("%Y/%m/%d %H:%M:%S")}'                                            
                    f'\n價格:{market_price}$'
                    f'\n數量:{quantity}'
                    f'\n價值:{round(exchange_quantity, 2)}$'
                    f'\n平倉原因:{reason}'                                   
                )                                 
                if position["side"] != "" :
                    message += ( f'\n剩餘持倉數量:{float(position["size"])}'
                                f'\n剩餘持倉價值:{round(float(position["positionValue"]), 2)}$'               
                    )
                print(message)
                bybit.send_line_message(self.line_key, message)  
                
        except Exception as err:
            raise Exception(err)

    def set_stop_profit(self, bybit) :
        position= bybit.get_position(self.pair)                 
        tpSize = float(
            bybit.convert_amount_to_precision(self.pair, float(position["size"]) * self.profit_size_percent)
        )    
        bybit.place_linear_stop_profit(self.pair, 'Partial', self.stop_profit, tpSize)
        
    def set_stop_loss(self, bybit, stop_loss_price) :
        position= bybit.get_position(self.pair)                 
        slSize = float(
            bybit.convert_amount_to_precision(self.pair, float(position["size"]))
        )    
        bybit.place_linear_stop_loss(self.pair, 'Partial', stop_loss_price, slSize)        
        
    def reset_stop_profit(self, bybit, side) :
        try :
            orderId = bybit.get_order_history_byside(self.pair, side, "PartialTakeProfit")['orderId']
            bybit.cancel_order(self.pair, orderId)
            
            position= bybit.get_position(self.pair)                 
            tpSize = float(
                bybit.convert_amount_to_precision(self.pair, float(position["size"]) * self.profit_size_percent)
            )    
            bybit.place_linear_stop_profit(self.pair, 'Partial', self.stop_profit, tpSize)       
        except Exception as err:
            print(err)    

    def reset_stop_loss(self, bybit, side, stop_loss_price) :
        try :
            orderId = bybit.get_order_history_byside(self.pair, side, "PartialStopLoss")['orderId']
            position= bybit.get_position(self.pair)                 
            slSize = float(
                bybit.convert_amount_to_precision(self.pair, float(position["size"]))
            )    
            bybit.place_linear_stop_loss(self.pair, 'Partial', stop_loss_price, slSize)                 
            bybit.cancel_order(self.pair, orderId)
        except Exception as err:
            print(err)              