import asyncio
import json
from playwright.async_api import async_playwright


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        url = "https://www.vanguardngr.com/search/crime"
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Wait for the search result links to appear
        await page.wait_for_selector("h2 a, h3 a", timeout=15000)

        # Grab headline links
        elements = await page.query_selector_all("h2 a, h3 a")

        headlines = []
        for element in elements:
            title = (await element.inner_text()).strip()
            link = await element.get_attribute("href")
            if title:
                headlines.append({"title": title, "link": link})
                print(title)

        # Save to JSON
        with open("headlines.json", "w", encoding="utf-8") as f:
            json.dump(headlines, f, ensure_ascii=False, indent=2)

        await browser.close()


asyncio.run(run())
