import os
import yagmail
from dotenv import load_dotenv

print("1. Loading env")

load_dotenv()

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

print("2. Email:", EMAIL)


def send_summary_email(receivers, subject, body):

    print("3. Function called")

    yag = yagmail.SMTP(
        user=EMAIL,
        password=APP_PASSWORD
    )

    print("4. SMTP object created")

    yag.send(
        to=receivers,
        subject=subject,
        contents=body
    )

    print("5. Email Sent")