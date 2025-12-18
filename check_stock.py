from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import csv
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 監視対象の商品ページ
URL = "https://item.rakuten.co.jp/taka-sake/garagara-kuji-2/"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# 履歴ファイル
LOG_FILE = "stock_log.csv"

# Gmail認証情報（GitHub Secretsから渡す）
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")

def get_stock():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=UA, locale="ja-JP")
        page = context.new_page()
        page.goto(URL, timeout=30000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        candidates = soup.find_all("div", class_=re.compile("text-display"))
        stock = None
        for div in candidates:
            text = div.get_text(strip=True)
            if re.fullmatch(r"\d+", text):
                stock = int(text)
                break

        browser.close()
        if stock is None:
            raise Exception("在庫数を示す数値が見つかりません")
        return stock

def save_and_check_change(stock):
    prev_stock = None
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            if rows:
                prev_stock = int(rows[-1][1])

    with open(LOG_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), stock])

    return prev_stock, stock

def send_gmail(subject, body, to=None):
    if not GMAIL_USER or not GMAIL_PASS:
        print("GMAIL_USER または GMAIL_PASS が設定されていません")
        return
    if to is None:
        to = GMAIL_USER  # 自分に送る

    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
    print("メール送信完了:", subject)

def main():
    stock = get_stock()
    print(f"在庫数: {stock}")

    prev_stock, current_stock = save_and_check_change(stock)

    if prev_stock is None:
        print("初回記録のため通知します（テスト用）")
        send_gmail(
            subject="【在庫チェック】初回記録",
            body=f"現在の在庫数: {current_stock}"
        )
    elif prev_stock != current_stock:
        msg = f"在庫数が変化しました: {prev_stock} → {current_stock}"
        print(msg)
        send_gmail(
            subject="【在庫変化あり】通知",
            body=msg
        )
    else:
        print("在庫数に変化なし")
        send_gmail(
            subject="【在庫変化なし】通知",
            body=f"在庫数は変化なし: {current_stock}"
        )

if __name__ == "__main__":
    main()
