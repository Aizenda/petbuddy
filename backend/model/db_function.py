from backend.model.db_connect import mysql_pool
from backend.model.data import get_clean_data

def create_table(query: str):
    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        print("建表失敗:", e)
    finally:
        cursor.close()
        conn.close()

create_table("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        phone VARCHAR(20) NOT NULL UNIQUE,
        is_phone_verified TINYINT(1) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
""")

create_table("""
    CREATA TABLE IF NOT EXISTS public(

             
             )
""")