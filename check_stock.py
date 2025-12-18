from playwright.sync_api import sync_playwright
import json
import re

URL = "https://item.rakuten.co.jp/kameyamadou/10013041/"

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

        match = re.search(r"__NEXT_DATA__\">({.*?})</script>", html)
        if not match:
            raise Exception("商品データが取得できません（NEXT_DATA欠落）")

        data = json.loads(match.group(1))

        try:
            product = (
                data["props"]["pageProps"]["catalog"]["product"]["variants"][0]
            )
        except:
            raise Exception("商品データの構造が取得できません")

        stock = product.get("stock", None)

        browser.close()

        if stock is None:
            raise Exception("在庫データが取得できません")

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
