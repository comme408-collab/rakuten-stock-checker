import requests
from bs4 import BeautifulSoup
import os

URL = "https://item.rakuten.co.jp/taka-sake/garagara-kuji-2/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_stock():
    res = requests.get(URL, headers=HEADERS, timeout=30)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # ★ 楽天ページ用（在庫数が「15」のように表示されている部分）
    for text in soup.stripped_strings:
        if text.isdigit():
            return int(text)

    raise Exception("在庫数が取得できませんでした")

def main():
    prev_stock = os.getenv("PREV_STOCK")
    current_stock = get_stock()

    print(f"current_stock={current_stock}")

    if prev_stock and int(prev_stock) != current_stock:
        print("STOCK_CHANGED=1")
    else:
        print("STOCK_CHANGED=0")

if __name__ == "__main__":
    main()
