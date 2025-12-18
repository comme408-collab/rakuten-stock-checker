import re
import requests

URL = "https://item.rakuten.co.jp/taka-sake/garagara-kuji-2/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

def get_stock():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()

    m = re.search(r'"stockCount":(\d+)', r.text)
    if not m:
        raise Exception("在庫データが見つかりません")

    return int(m.group(1))

def main():
    stock = get_stock()
    print(f"現在在庫数: {stock}")

if __name__ == "__main__":
    main()
