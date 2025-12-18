import requests

APP_ID = "YOUR_RAKUTEN_API_KEY"
ITEM_CODE = "taka-sake:garagara-kuji-2"

def get_stock():
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"
    params = {
        "applicationId": APP_ID,
        "itemCode": ITEM_CODE
    }
    res = requests.get(url, params=params)
    data = res.json()

    if "Items" not in data or len(data["Items"]) == 0:
        raise Exception("商品が取得できません")

    item = data["Items"][0]["Item"]

    stock = item.get("stockcount", None)
    if stock is None:
        raise Exception("在庫情報が取れません")

    return stock


def main():
    stock = get_stock()
    print(f"現在の在庫数: {stock}")


if __name__ == "__main__":
    main()
