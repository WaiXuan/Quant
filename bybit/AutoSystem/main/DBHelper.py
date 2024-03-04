import pymssql

class DBHelper:
    def __init__(self):
        self.server = 'localhost'
        self.username = 'WeiXuan'
        self.password = 'ilove524'
        self.database = 'Quantitative'
        self.conn = None

    def connect(self):
        try:
            self.conn = pymssql.connect(
                server=self.server,
                user=self.username,
                password=self.password,
                database=self.database
            )
            return self.conn  # 返回數據庫連接對象
        except Exception as e:
            print(f"連接錯誤: {str(e)}")
        
    def execute_query(self, query):
        try:
            self.conn = self.connect()
            cursor = self.conn.cursor()  # 從連接中創建游標
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"查詢執行錯誤: {str(e)}")

    def execute_sp(self, sp_name, param_dict):
        try:
            self.conn = self.connect()
            cursor = self.conn.cursor()
            
            # 將字典的值轉換為元組
            params = tuple(param_dict.values())
            cursor.callproc(sp_name, (params)) 
            
            # 提交更改
            self.conn.commit()
            # result = cursor.fetchone()
            cursor.close()
            # return result
        except Exception as e:
            print(f"執行sp發生錯誤: {str(e)}")


    def close(self):
        if self.conn:
            self.conn.close()
            print("連接已關閉")