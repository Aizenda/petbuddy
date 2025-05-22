from mysql.connector import pooling, Error
import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnectionError(Exception):
    def __init__(self, message):
        super().__init__(message)


class MySQLPool:
    def __init__(self):
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="mypool",
                pool_size=10,
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME")
            )
        except Error as err:
            print(f"資料庫連線池初始化失敗: {err}")
            self.pool = None
            raise DatabaseConnectionError(f"資料庫初始化錯誤: {err}")

    def get_connection(self):
        if self.pool is None:
            raise DatabaseConnectionError("資料庫連線池未初始化")

        try:
            conn = self.pool.get_connection()
            if not conn.is_connected():
                raise DatabaseConnectionError("資料庫連線失敗")
            return conn
        except Error as err:
            raise DatabaseConnectionError(f"資料庫連線錯誤: {err}")


# 初始化 MySQL 連線池
mysql_pool = MySQLPool()