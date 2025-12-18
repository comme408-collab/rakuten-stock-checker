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

        # 在庫数が入っているdivを探す
        stock_div = soup.find("div", class_=re.compile("text-display"))
        if not stock_div:
            browser.close()
            raise Exception("在庫数を示す要素が見つかりません")

        try:
            stock = int(stock_div.get_text(strip=True))
        except ValueError:
            browser.close()
            raise Exception("在庫数を数値に変換できません")

        browser.close()
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
