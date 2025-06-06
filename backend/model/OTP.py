from twilio.rest import Client
import os, random
from dotenv import load_dotenv
from .redis_sever import *

load_dotenv()

class OTPService:

    def __init__(self):
        self.client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.redis = Redis_OTP() 

    def generate_otp(self) -> int:
        return random.randint(100000, 999999)

    def send_otp(self, phone_number: str):
        formatted_phone = self._format_phone_number(phone_number)
        otp = self.generate_otp()
        print(otp)
        message = f"您的簡訊驗證碼為：{otp}"

        self.redis.set_otp(phone_number, otp)

        message_response = self.client.messages.create(
            body=message,
            from_=self.twilio_number,
            to=formatted_phone
        )
        return message_response.sid  # 可選回傳

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
