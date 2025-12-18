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

    # 在庫部分を正確に抽出
    stock_element = soup.select_one("div.text-display--3jedW.type-body--27DSG.size-medium--3VTRm.align-left--3uu15.color-gray-darker--3K2Fe.layout-block--3uuSk")
    if not stock_element:
        raise Exception("在庫データの要素が見つかりませんでした")

    stock_text = stock_element.text.strip()

    if not stock_text.isdigit():
        raise Exception(f"在庫数が数値ではありません: {stock_text}")

    return int(stock_text)

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
