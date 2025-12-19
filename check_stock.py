from playwright.sync_api import sync_playwright
import re
import csv
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

URLS = [
    "https://item.rakuten.co.jp/taka-sake/garagara-kuji-1/",
    "https://item.rakuten.co.jp/taka-sake/garagara-kuji-2/",
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")

STOCK_KEYWORDS = ["在庫数", "在庫", "残り", "残数", "販売可能", "個"]

def extract_stock_line_based(text: str) -> int | None:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        if any(lbl in line for lbl in STOCK_KEYWORDS):
            for j in range(1, 3):
                if i + j < len(lines):
                    m = re.fullmatch(r"\d{1,5}", lines[i + j])
                    if m:
                        return int(m.group(0))
    for line in lines:
        if any(lbl in line for lbl in STOCK_KEYWORDS):
            m = re.search(r"\d{1,5}", line)
            if m:
                return int(m.group(0))
    return None

def get_stock_once(url: str) -> int | None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=UA, locale="ja-JP")
        page = context.new_page()
        page.goto(url, timeout=45000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")

        text = page.inner_text("body")
        stock = extract_stock_line_based(text)
        browser.close()
        return stock

def send_gmail(subject, body, to=None):
    if not GMAIL_USER or not GMAIL_PASS:
        print("GMAIL_USER または GMAIL_PASS が設定されていません")
        return
    if to is None:
        to = GMAIL_USER

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
    for url in URLS:
        product_id = url.strip("/").split("/")[-1]
        log_file = f"stock_log_{product_id}.csv"

        prev_stock = None
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                rows = [r for r in csv.reader(f) if r]
                if rows:
                    try:
                        prev_stock = int(rows[-1][1])
                    except:
                        prev_stock = None

        current_stock = get_stock_once(url)
        print(f"{url} の在庫数: {current_stock}")

        if prev_stock is None:
            send_gmail(
                subject=f"【在庫チェック 初回記録】{url}",
                body=f"現在の在庫数: {current_stock}\n\nページURL: {url}"
            )
        elif prev_stock != current_stock:
            send_gmail(
                subject=f"【在庫変化あり】{url}",
                body=f"在庫数が変化しました: {prev_stock} → {current_stock}\n\nページURL: {url}"
            )
        else:
            send_gmail(
                subject=f"【在庫変化なし】{url}",
                body=f"在庫数は変化なし: {current_stock}\n\nページURL: {url}"
            )

        with open(log_file, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), current_stock])

if __name__ == "__main__":
    main()
