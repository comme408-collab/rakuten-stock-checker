from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://item.rakuten.co.jp/taka-sake/garagara-kuji-2/"

def get_stock():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, timeout=60000)

        html = page.content()
        browser.close()

        soup = BeautifulSoup(html, "html.parser")

        # 数字のみのDIVから在庫を抽出
        for div in soup.find_all("div"):
            txt = div.text.strip()
            if txt.isdigit():
                return int(txt)

        raise Exception("在庫が見つかりません")


def main():
    stock = get_stock()
    print(f"現在の在庫: {stock}")


if __name__ == "__main__":
    main()
