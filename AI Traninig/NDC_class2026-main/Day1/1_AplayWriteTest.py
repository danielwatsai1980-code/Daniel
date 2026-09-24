from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright


#put your search query here
SEARCH_QUERY = "boko haram"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(f"https://duckduckgo.com/?q={quote_plus(SEARCH_QUERY)}")
        page.wait_for_selector("article h2")

        results = page.query_selector_all("article h2")
        for i, result in enumerate(results, start=1):
            print(f"{i}. {result.inner_text()}")

        browser.close()


if __name__ == "__main__":
    main()

