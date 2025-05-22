import boto3, os, random
from dotenv import load_dotenv
from .redis_sever import *

load_dotenv()

class OTPService:

    def __init__(self):
        self.client = boto3.client(
            "sns",
            aws_access_key_id=os.getenv("SNS_Access_key"),
            aws_secret_access_key=os.getenv("SNS_Secret_acces_key"),
            region_name=os.getenv("AWS_REGION")
        )
        self.redis = Redis_OTP() 

    def generate_otp(self) -> int:
        return random.randint(100000, 999999)

    def send_otp(self, phone_number: str):
        formatted_phone = self._format_phone_number(phone_number)
        otp = self.generate_otp()
        message = f"您的簡訊驗證碼為：{otp}"
        print(otp)

        self.redis.set_otp(phone_number, otp) 

        response = self.client.publish(
            PhoneNumber=formatted_phone,
            Message=message
        )
        return response

    def verify_otp(self, phone_number: str, user_input: str) -> bool:
        otp_stored = self.redis.get_otp(phone_number) 
        if otp_stored and otp_stored == user_input:
            self.redis.delete_otp(phone_number)
            return True
        return False

    def _format_phone_number(self, phone_number: str) -> str:
        phone_number = phone_number.strip().replace("-", "").replace(" ", "")
        if phone_number.startswith("09"):
            return "+886" + phone_number[1:]
        elif phone_number.startswith("+886"):
            return phone_number
        else:
            raise ValueError("無效的台灣手機號碼格式")