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

    def insert_send(self, data: dict) -> int:
        sql = """
        INSERT INTO send (
            user_id, pet_name, pet_breed, pet_kind, pet_sex,
            pet_bodytype, pet_colour, pet_place, pet_describe,
            pet_ligation_status, pet_age
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data["user_id"], data["pet_name"], data["pet_breed"], data["pet_kind"],
            data["pet_sex"], data["pet_bodytype"], data["pet_colour"],
            data["pet_place"], data["pet_describe"], data["pet_ligation_status"], data["pet_age"]
        )
        self.cursor.execute(sql, values)
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_img(self, send_id: int, url: str):
        self.cursor.execute("INSERT INTO imgurl (send_id, img_url) VALUES (%s, %s)", (send_id, url))
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()