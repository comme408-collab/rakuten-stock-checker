import re
import requests

URL = "https://item.rakuten.co.jp/taka-sake/garagara-kuji-2/"

def get_stock():
    r = requests.get(URL, timeout=10)
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
