import requests
from bs4 import BeautifulSoup
import re

URL = "https://item.rakuten.co.jp/taka-sake/garagara-kuji-2/"

def get_stock():
    # ---- ページ取得 ----
    res = requests.get(URL, headers={
        "User-Agent": "Mozilla/5.0"
    })
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    # ---- 「数字のみの div」を幅広く取得 ----
    possible_divs = soup.find_all("div")

    for div in possible_divs:
        if div.text.strip().isdigit():
            # 見つけた数字を返す
            return int(div.text.strip())

    # ---- 部分一致クラス絞り込み版 ----
    stock_element = soup.find("div", class_=lambda x: x and "text-display" in x)
    if stock_element:
        stock = stock_element.text.strip()
        if stock.isdigit():
            return int(stock)

    # ---- 正規表現で拾う版 ----
    numbers = re.findall(r'>\s*(\d{1,4})\s*<', res.text)
    if numbers:
        return int(numbers[0])

    # ---- どれもダメなら失敗 ----
    raise Exception("在庫数が取得できませんでした")


def main():
    stock = get_stock()
    print(f"現在の在庫数: {stock}")


if __name__ == "__main__":
    main()
