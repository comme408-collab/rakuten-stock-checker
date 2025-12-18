import requests
import json
import re

URL = "https://item.rakuten.co.jp/taka-sake/garagara-kuji-2/"

def get_stock():
    # --- HTML取得 ---
    res = requests.get(URL, headers={
        "User-Agent": "Mozilla/5.0"
    })
    res.raise_for_status()

    html = res.text

    # --- JSONを含む script を抽出 ---
    match = re.search(r'__RUC_ITEM__\s*=\s*(\{.*?\});', html, re.DOTALL)
    if not match:
        raise Exception("商品データJSONが見つかりません")

    data = json.loads(match.group(1))

    # --- 在庫数取得 ---
    stock = data["displayInfo"]["stockCount"]

    return stock


def main():
    stock = get_stock()
    print(f"現在の在庫数: {stock}")


if __name__ == "__main__":
    main()
