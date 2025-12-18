import requests
from bs4 import BeautifulSoup
import os
import smtplib
from email.mime.text import MIMEText

URL = "https://item.rakuten.co.jp/taka-sake/garagara-kuji-2/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_stock():
    res = requests.get(URL, headers=HEADERS, timeout=30)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    for text in soup.stripped_strings:
        if text.isdigit():
            return int(text)

    raise Exception("在庫数が取得できませんでした")

def send_mail(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.environ["EMAIL_FROM"]
    msg["To"] = os.environ["EMAIL_TO"]

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(os.environ["EMAIL_FROM"], os.environ["EMAIL_PASS"])
        smtp.send_message(msg)

def main():
    current_stock = get_stock()
    prev_stock = os.getenv("PREV_STOCK")

    if prev_stock and int(prev_stock) != current_stock:
        send_mail(
            "【楽天】在庫数が変わりました",
            f"URL: {URL}\n前回: {prev_stock}\n今回: {current_stock}"
        )

    print(f"PREV_STOCK={current_stock}")

if __name__ == "__main__":
    main()
