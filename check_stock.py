from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import csv
import os
from datetime import datetime
import requests

URL = "https://item.rakuten.co.jp/taka-sake/garagara-kuji-2/"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

LOG_FILE = "stock_log.csv"
LINE_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")

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

def send_line_notify(message):
    if not LINE_TOKEN:
        print("LINE_NOTIFY_TOKEN が設定されていません")
        return
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
    data = {"message": message}
    response = requests.post(url, headers=headers, data=data)
    print("LINE Notify response:", response.status_code, response.text)

def main():
    stock = get_stock()
    print(f"在庫数: {stock}")

    prev_stock, current_stock = save_and_check_change(stock)

    if prev_stock is None:
        print("初回記録のため通知しません")
        send_line_notify("テスト通知: LINE連携確認")  # ← テスト用通知
    elif prev_stock != current_stock:
        msg = f"在庫数が変化しました: {prev_stock} → {current_stock}"
        print(msg)
        send_line_notify(msg)
    else:
        print("在庫数に変化なし")

if __name__ == "__main__":
    main()
