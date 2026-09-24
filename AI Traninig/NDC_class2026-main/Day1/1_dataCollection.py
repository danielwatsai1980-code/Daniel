

import asyncio
import json
import re
from datetime import datetime, timezone
from playwright.async_api import async_playwright

# Common Nigerian states/cities used to guess the location referenced in a headline.
KNOWN_LOCATIONS = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue",
    "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu",
    "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi",
    "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo",
    "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara", "Abuja",
    "Ibadan", "Port Harcourt", "Kaduna", "Aba", "Onitsha", "Warri", "Jos",
    "Maiduguri", "Nigeria","Minna"
]


# Keywords used to keep only crime-related headlines.
CRIME_KEYWORDS = [
    "kill", "murder", "kidnap", "abduct", "robber", "armed robbery", "theft",
    "steal", "gun", "gunmen", "shoot", "attack", "assault", "rape", "fraud",
    "scam", "arrest", "police", "suspect", "crime", "criminal", "bandit",
    "terror", "cult", "drug", "traffick", "burglar", "assassinat", "violence",
    "ritual", "corpse", "body", "raid", "looting", "vandal", "extort", "ransom",
]


def detect_location(text):
    """Return the first known location mentioned in the headline, else None."""
    for location in KNOWN_LOCATIONS:
        if re.search(rf"\b{re.escape(location)}\b", text, re.IGNORECASE):
            return location
    return None


def is_crime_related(text):
    """Return True if the headline mentions any crime-related keyword."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in CRIME_KEYWORDS)


# Matches a visible date like "September 03, 2026".
DATE_TEXT_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b"
)


def date_from_url(link):
    """Extract a YYYY-MM date from a Vanguard article URL (e.g. /2026/09/...)."""
    if not link:
        return None
    match = re.search(r"/(\d{4})/(\d{2})/", link)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None


async def extract_date(element, link):
    """Return the occurrence date from the nearby DOM text, falling back to the URL."""
    try:
        container_text = await element.evaluate(
            "el => { const c = el.closest('article') || el.parentElement; return c ? c.innerText : ''; }"
        )
    except Exception:
        container_text = ""
    match = DATE_TEXT_RE.search(container_text or "")
    if match:
        return match.group(0)
    return date_from_url(link)


async def block_resources(page):
    """Abort image/stylesheet/media/font requests on the given page to speed up loading."""
    await page.route(
        "**/*",
        lambda route: route.abort()
        if route.request.resource_type in ["image", "stylesheet", "media", "font"]
        else route.continue_(),
    )


async def detect_location_from_content(context, link, timeout=15000):
    """Open the article, read its body text and return the first known location mentioned."""
    if not link:
        return None
    article_page = None
    try:
        article_page = await context.new_page()
        await block_resources(article_page)
        await article_page.goto(link, wait_until="domcontentloaded", timeout=timeout)
        for selector in ["article", ".entry-content", ".post-content", "main", "body"]:
            content_element = await article_page.query_selector(selector)
            if content_element:
                text = await content_element.inner_text()
                if text.strip():
                    return detect_location(text)
        return None
    except Exception:
        return None
    finally:
        if article_page:
            await article_page.close()


async def scrape_source(context, source_name, url, seen_titles):
    """Scrape one news site's headline listing and return the crime-related ones."""
    page = await context.new_page()
    await block_resources(page)
    print(f"Navigating to {url}...")

    headlines = []
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Note: sites vary in markup; this generic selector assumes headlines
        # live inside <h2>/<h3> elements containing an <a> tag (common on WordPress sites).
        headline_elements = await page.query_selector_all("h2 a, h3 a")

        print(f"\n--- Scanning {len(headline_elements)} headlines from {source_name} ---")

        for element in headline_elements:
            title = await element.inner_text()
            link = await element.get_attribute("href")

            title = title.strip()

            if not title or title in seen_titles:
                continue
            if not is_crime_related(title):
                continue

            seen_titles.add(title)
            location = detect_location(title)
            if location is None:
                location = await detect_location_from_content(context, link)
            date = await extract_date(element, link)
            headlines.append({
                "source": source_name,
                "title": title,
                "link": link,
                "location": location,
                "date": date,
            })
            print(f"{len(headlines)}. [{source_name}] {title}")
            print(f"   Link: {link}")
            print(f"   Location: {location}")
            print(f"   Date: {date}\n")
    except Exception as e:
        print(f"An error occurred while scraping {source_name}: {e}")
    finally:
        await page.close()

    return headlines


async def run():
    # News sites to scan for crime headlines.
    SOURCES = [
        {"name": "Vanguard", "url": "https://www.vanguardngr.com/search/crime"},
        {"name": "Punch", "url": "https://punchng.com/topics/crime/"},
        {"name": "Premium Times", "url": "https://www.premiumtimesng.com/?s=crime"},
    ]

    async with async_playwright() as p:
        # 1. Launch a headless browser (runs invisibly in the background)
        browser = await p.chromium.launch(headless=True)
        
        # 2. Create an isolated browser context (like a fresh incognito window)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            # 3. Scrape each source in turn, skipping titles already seen from a previous source
            seen_titles = set()
            all_headlines = []
            for source in SOURCES:
                all_headlines.extend(
                    await scrape_source(context, source["name"], source["url"], seen_titles)
                )

            # 4. Assign a final rank across all combined sources
            for rank, item in enumerate(all_headlines, start=1):
                item["rank"] = rank

            # 5. Save the collected crime headlines to a JSON file
            output = {
                "sources": [s["url"] for s in SOURCES],
                "category": "crime",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "count": len(all_headlines),
                "headlines": all_headlines,
            }
            with open("crime_headlines.json", "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(all_headlines)} crime headlines to crime_headlines.json")

        except Exception as e:
            print(f"An error occurred: {e}")
            
        finally:
            # 6. Always close the browser cleanly
            await browser.close()

# Run the asynchronous script
asyncio.run(run())
# Headline for all piltical news

