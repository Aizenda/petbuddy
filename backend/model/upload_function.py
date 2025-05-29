import boto3,os,uuid
from io import BytesIO
from dotenv import load_dotenv
from .db_connect import mysql_pool

load_dotenv()

access_key = os.getenv("Access_key")
secret_key = os.getenv("Secret_access_key")
AWS_Region = os.getenv("AWS_Region")


class Uploader():
	def __init__(self):
		self.s3 = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=AWS_Region
        )
    
	async def upload_file(self, file, bucket):
		try:
			unique_file_name = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"

			file_content = await file.read()
			
			file_bytes_io = BytesIO(file_content)
			
			self.s3.upload_fileobj(file_bytes_io, bucket, f"text/{unique_file_name}")
			
			file_url = self.get_file_url(bucket, f"text/{unique_file_name}")
			return file_url
		
		except Exception as e:
			print("Upload failed:", e)
			return None

	def get_file_url(self, bucket, key):
		url = f"https://d3v5oek5w3gawn.cloudfront.net/{key}"
		return url
	

class UploadText:
    def __init__(self):

        self.conn = mysql_pool.get_connection()
        self.cursor = self.conn.cursor()

    def create_table(self):
        try:
            create_query = """
            CREATE TABLE IF NOT EXISTS send (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,  -- 加上這一行
                pet_name VARCHAR(255) NOT NULL,
                pet_breed VARCHAR(50) NOT NULL,
                pet_kind VARCHAR(50) NOT NULL,
                pet_sex VARCHAR(50) NOT NULL,
                pet_bodytype VARCHAR(50) NOT NULL,
                pet_colour VARCHAR(50) NOT NULL,
                pet_place VARCHAR(50) NOT NULL,
                pet_describe VARCHAR(255) NOT NULL,
                pet_ligation_status VARCHAR(50) NOT NULL,
                pet_img_url VARCHAR(255) NOT NULL,
                created_at DATE DEFAULT (CURRENT_DATE),
                CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
            );
            """
            self.cursor.execute(create_query)
            self.conn.commit()
        except Exception as e:
            print("Failed to create table:", e)
            self.conn.rollback()

    def insert_text(self, data: dict, file_url: str):
        try:
            insert_query = """
            INSERT INTO send (
                user_id,
                pet_name,
                pet_breed,
                pet_kind,
                pet_sex,
                pet_bodytype,
                pet_colour,
                pet_place,
                pet_describe,
                pet_ligation_status,
                pet_img_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(insert_query, (
                data["user_id"],
                data["pet_name"],
                data["pet_breed"],
                data["pet_kind"],
                data["pet_sex"],
                data["pet_bodytype"],
                data["pet_colour"],
                data["pet_place"],
                data["pet_describe"],
                data["pet_ligation_status"],
                file_url
            ))
            self.conn.commit()
        except Exception as e:
            print(f"Error occurred: {e}")
            self.conn.rollback()
    
    @classmethod
    def select(cls):
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            select_query = """
            SELECT id,text, file_url FROM send
            ORDER BY id DESC;
            """
            cursor.execute(select_query) 
            data = cursor.fetchall()   
            return data
        
        except Exception as e:
            print("Error during SELECT:", e)
            return []
        
        finally:
            cursor.close()
            conn.close()

 
    def close(self):
    
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()