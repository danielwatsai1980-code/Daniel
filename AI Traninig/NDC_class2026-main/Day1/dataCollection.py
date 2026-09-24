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
    "Maiduguri", "Nigeria",
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


async def run():
    async with async_playwright() as p:
        # 1. Launch a headless browser (runs invisibly in the background)
        browser = await p.chromium.launch(headless=True)
        
        # 2. Create an isolated browser context (like a fresh incognito window)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # 3. Create a new page
        page = await context.new_page()
        
        # 4. OPTIMIZATION: Block images and stylesheets to save bandwidth and speed up loading
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "media", "font"] else route.continue_())

        # Target URL (Vanguard crime search page)
        url = "https://www.vanguardngr.com/search/crime"
        print(f"Navigating to {url}...")
        
        try:
            # Go to the website and wait until the core network connections are quiet
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # 5. Extract headlines. 
            # Note: You will need to inspect the target site's HTML to update this CSS selector.
            # For this example, we assume headlines are inside <h2> elements containing an <a> tag.
            headline_elements = await page.query_selector_all("h2 a, h3 a")
            
            print(f"\n--- Scanning {len(headline_elements)} headlines for crime news ---")
            
            # 6. Loop through elements, keeping only crime-related headlines
            headlines = []
            seen_titles = set()
            for element in headline_elements:
                title = await element.inner_text()
                link = await element.get_attribute("href")
                
                # Clean up whitespaces
                title = title.strip()
                
                if not title or title in seen_titles:
                    continue
                if not is_crime_related(title):
                    continue

                seen_titles.add(title)
                location = detect_location(title)
                date = await extract_date(element, link)
                headlines.append({
                    "rank": len(headlines) + 1,
                    "title": title,
                    "link": link,
                    "location": location,
                    "date": date,
                })
                print(f"{len(headlines)}. {title}")
                print(f"   Link: {link}")
                print(f"   Location: {location}")
                print(f"   Date: {date}\n")

            # 7. Save the collected crime headlines to a JSON file
            output = {
                "source": url,
                "category": "crime",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "count": len(headlines),
                "headlines": headlines,
            }
            with open("crime_headlines.json", "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(headlines)} crime headlines to crime_headlines.json")
                    
        except Exception as e:
            print(f"An error occurred: {e}")
            
        finally:
            # 8. Always close the browser cleanly
            await browser.close()

# Run the asynchronous script
asyncio.run(run())
