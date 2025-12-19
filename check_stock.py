from playwright.sync_api import sync_playwright
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

LOG_FILE = "stock_log.csv"

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")

# 異常値判定のしきい値（例：前回との差が大きい場合は再取得して確認）
ANOMALY_DELTA = 200  # 例：200以上のジャンプは疑う
MAX_STOCK_REASONABLE = 2000  # 異常に大きい値は除外（ページ仕様に合わせて調整）

def extract_stock_line_based(text: str) -> int | None:
    """
    行ベースで抽出：
    - 「在庫数」「在庫」「残り」などのラベルがある行の直後行から、純粋な数字のみ抽出
    - 余計な連結を避けるため、1行分の数字のみを対象
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    label_indices = []
    labels = ["在庫数", "在庫", "残り", "残数", "販売可能"]
    for i, line in enumerate(lines):
        if any(lbl in line for lbl in labels):
            label_indices.append(i)

    for idx in label_indices:
        # 直後の数行をチェック（0〜2行先まで）
        for j in range(1, 3):
            if idx + j < len(lines):
                m = re.fullmatch(r"\d{1,5}", lines[idx + j])
                if m:
                    num = int(m.group(0))
                    # 異常に大きい在庫は除外
                    if num <= MAX_STOCK_REASONABLE:
                        return num

    # ラベル近傍で見つからない場合のフォールバック：
    # 「個」「在庫」などを含む行から最も自然な数字を選択
    candidates = []
    for line in lines:
        nums = re.findall(r"\d{1,5}", line)
        if nums:
            score = 0
            if any(lbl in line for lbl in labels): score += 3
            if "個" in line: score += 2
            for n in nums:
                num = int(n)
                if num <= MAX_STOCK_REASONABLE:
                    # 数量入力の既定値っぽい小さすぎる値は減点
                    local_score = score - (2 if num <= 2 else 0)
                    candidates.append((local_score, num, line))
    if candidates:
        chosen = max(candidates, key=lambda x: (x[0], x[1]))
        return chosen[1]

    return None

def fetch_text(page) -> str:
    # bodyのレンダリング完了後のテキストを取得
    return page.inner_text("body")

def get_stock_once() -> int | None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=UA, locale="ja-JP", viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.goto(URL, timeout=45000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")
        text = fetch_text(page)
        # print("ページテキスト先頭:", text[:500])  # 必要ならデバッグ
        stock = extract_stock_line_based(text)
        # 必要ならHTML保存して解析
        # html = page.content()
        # with open("debug.html", "w", encoding="utf-8") as f:
        #     f.write(html)
        browser.close()
        return stock

def get_stock(prev_stock: int | None = None) -> int:
    """
    1回取得→異常なジャンプならもう1回取得して一致確認。
    一致しない場合は前回値を維持（通知ノイズを防ぐ）。
    """
    s1 = get_stock_once()
    if s1 is None:
        raise Exception("在庫数の抽出に失敗しました（s1）")

    # 前回値がある場合のみ異常ジャンプ判定
    if prev_stock is not None and abs(s1 - prev_stock) >= ANOMALY_DELTA:
        s2 = get_stock_once()
        if s2 is None:
            raise Exception("在庫数の抽出に失敗しました（s2）")
        # 2回目と一致しない、またはどちらかが極端に大きい場合は前回値を採用
        if s1 != s2 or s1 > MAX_STOCK_REASONABLE or s2 > MAX_STOCK_REASONABLE:
            print(f"[guard] 異常ジャンプ検出: prev={prev_stock}, s1={s1}, s2={s2} → 前回値を維持")
            return prev_stock
        # 一致したら採用
        return s2

    return s1

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
    # 前回値を先に読み込む（異常ジャンプガードのため）
    prev = None
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            if rows:
                prev = int(rows[-1][1])

    current = get_stock(prev_stock=prev)
    print(f"在庫数: {current}")
    prev_stock, current_stock = save_and_check_change(current)

    if prev_stock is None:
        print("初回記録のため通知します（テスト用）")
        send_gmail(
            subject="【在庫チェック】初回記録",
            body=f"現在の在庫数: {current_stock}\n\nページURL: {URL}"
        )
    elif prev_stock != current_stock:
        msg = f"在庫数が変化しました: {prev_stock} → {current_stock}"
        print(msg)
        send_gmail(
            subject="【在庫変化あり】通知",
            body=f"{msg}\n\nページURL: {URL}"
        )
    else:
        print("在庫数に変化なし")
        send_gmail(
            subject="【在庫変化なし】通知",
            body=f"在庫数は変化なし: {current_stock}\n\nページURL: {URL}"
        )

if __name__ == "__main__":
    main()
