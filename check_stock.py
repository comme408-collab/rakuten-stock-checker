from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

URL = "https://item.rakuten.co.jp/taka-sake/garagara-kuji-2/"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

def get_stock():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=UA,
            locale="ja-JP",
            java_script_enabled=True,
        )
        page = context.new_page()
        page.goto(URL, timeout=30000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        # text-display クラスを持つ要素をすべて取得
        candidates = soup.find_all("div", class_=re.compile("text-display"))

        stock = None
        for div in candidates:
            text = div.get_text(strip=True)
            # 数字だけの要素を探す
            if re.fullmatch(r"\d+", text):
                stock = int(text)
                break

        browser.close()

        if stock is None:
            raise Exception("在庫数を示す数値が見つかりません")

        return stock

def main():
    stock = get_stock()
    print(f"在庫数: {stock}")

    if stock > 0:
        print("★ 在庫あり！")
    else:
        print("在庫なし")

if __name__ == "__main__":
    main()
