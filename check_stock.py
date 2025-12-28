from playwright.sync_api import sync_playwright
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

THRESHOLD = 10  # 10以下になったら通知


# -------------------------
# Playwright で在庫を DOM から直接取得（最強・最安定）
# -------------------------
def get_stock_once(url: str) -> int | None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=UA, locale="ja-JP")
        page = context.new_page()
        page.goto(url, timeout=45000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")

        try:
            # 在庫数の div（2つ目）を直接取得
            stock_text = page.inner_text(
                "td.normal-reserve-inventory div:nth-of-type(2)"
            ).strip()

            if stock_text.isdigit():
                return int(stock_text)

        except Exception as e:
            print("在庫取得エラー:", e)

        return None


# -------------------------
# Gmail 通知
# -------------------------
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


# -------------------------
# メイン処理
# -------------------------
def main():
    for url in URLS:
        product_id = url.strip("/").split("/")[-1]
        log_file = f"stock_log_{product_id}.csv"

        # --- 前回在庫の読み込み ---
        prev_stock = None
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                rows = [r for r in csv.reader(f) if r]
                if rows:
                    last_value = rows[-1][1]
                    prev_stock = int(last_value) if last_value.isdigit() else None

        # --- 今回の在庫取得 ---
        current_stock = get_stock_once(url)
        print(f"{url} の在庫数: {current_stock}")

        # -------------------------
        # 通知ロジック（しきい値対応・最終安定版）
        # -------------------------

        # 初回（ただし在庫がしきい値以下のときだけ通知）
        if prev_stock is None:
            if current_stock is not None and current_stock <= THRESHOLD:
                send_gmail(
                    subject=f"【在庫チェック 初回記録】{url}",
                    body=f"現在の在庫数: {current_stock}\n\nページURL: {url}"
                )

        else:
            # 売り切れになった瞬間（数値 → None）
            if prev_stock is not None and current_stock is None:
                send_gmail(
                    subject=f"【売り切れ】{url}",
                    body=f"在庫が売り切れになりました: {prev_stock} → 売り切れ\n\nページURL: {url}"
                )

            # 再入荷（None → 数値）
            elif prev_stock is None and current_stock is not None:
                if current_stock <= THRESHOLD:
                    send_gmail(
                        subject=f"【再入荷】{url}",
                        body=f"在庫が復活しました: 売り切れ → {current_stock}\n\nページURL: {url}"
                    )

            # 数値同士の変化
            elif (
                prev_stock is not None
                and current_stock is not None
                and prev_stock != current_stock
            ):
                # しきい値をまたいだときだけ通知
                if prev_stock > THRESHOLD and current_stock <= THRESHOLD:
                    send_gmail(
                        subject=f"【在庫が少なくなりました】{url}",
                        body=f"在庫数が {prev_stock} → {current_stock} に減りました（しきい値 {THRESHOLD} 以下）\n\nページURL: {url}"
                    )

        # --- ログ更新（None は空文字で保存） ---
        value = "" if current_stock is None else current_stock
        with open(log_file, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), value])


if __name__ == "__main__":
    main()
