"""
Lyn Alden premium newsletter scraper.
Saves articles as markdown with frontmatter to investment_research/lyn-alden/scraped/
Filename format: TITLE-YYMMDD.md

Usage:
    python scraper.py          # scrape latest 10
    python scraper.py --all    # scrape all (1 year = ~26 articles, use carefully)
    python scraper.py --limit 5
"""
import argparse
import asyncio
import random
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

from markdownify import markdownify
from playwright.async_api import async_playwright

LOGIN_URL = "https://www.lynalden.com/login/"
MEMBERS_URL = "https://www.lynalden.com/members/"
EMAIL = "catalin.mates@gmail.com"
PASSWORD = "Vancouver2025!"

OUTPUT_DIR = Path(__file__).parent.parent.parent / "investment_research" / "lyn-alden" / "scraped"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Only scrape articles from the last 12 months
CUTOFF_DATE = datetime.now() - timedelta(days=365)


async def human_delay(min_s=8, max_s=20):
    delay = random.uniform(min_s, max_s)
    print(f"  (waiting {delay:.1f}s...)")
    await asyncio.sleep(delay)


async def login(page):
    await page.goto(LOGIN_URL, timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(2, 4))
    await page.fill('input[name="rcp_user_login"]', EMAIL)
    await asyncio.sleep(random.uniform(1, 2))
    await page.fill('input[name="rcp_user_pass"]', PASSWORD)
    await asyncio.sleep(random.uniform(1, 2))
    await page.click('input[id="rcp_login_submit"]')
    await page.wait_for_load_state("domcontentloaded")
    await asyncio.sleep(random.uniform(3, 5))
    assert "members" in page.url, f"Login failed, landed on {page.url}"
    print("✓ Logged in")


def parse_article_date(href: str) -> datetime | None:
    """Extract date from URL like premium-2026-5-10."""
    m = re.search(r"premium-(\d{4})-(\d{1,2})-(\d{1,2})", href)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def make_filename(title: str, date: datetime) -> str:
    """YYMMDD-title.md"""
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    slug = re.sub(r"-+", "-", slug)[:60]
    date_str = date.strftime("%y%m%d")
    return f"{date_str}-{slug}.md"


def extract_article_content(html: str, title: str, date: datetime, url: str) -> str:
    """Convert article HTML to markdown with frontmatter."""
    md = markdownify(html, heading_style="ATX", strip=["script", "style", "nav", "footer"])
    # Clean up excessive blank lines
    md = re.sub(r"\n{3,}", "\n\n", md).strip()

    frontmatter = f"""---
title: "{title}"
date: "{date.strftime('%Y-%m-%d')}"
source_url: "{url}"
analyst: "Lyn Alden"
type: "premium_newsletter"
---

"""
    return frontmatter + f"# {title}\n\n" + md


async def scrape_article(page, url: str, title: str, date: datetime) -> str | None:
    filename = make_filename(title, date)
    output_path = OUTPUT_DIR / filename

    if output_path.exists():
        print(f"  ✓ Already saved: {filename}")
        return filename

    print(f"  Fetching: {title}")
    await page.goto(url, timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(3, 6))

    # Extract main article content
    content_html = await page.eval_on_selector(
        "article, .entry-content, .post-content, main",
        "el => el.innerHTML",
    )

    md_content = extract_article_content(content_html, title, date, url)
    output_path.write_text(md_content, encoding="utf-8")
    print(f"  ✓ Saved: {filename} ({len(md_content)} chars)")
    return filename


async def get_article_links(page) -> list[dict]:
    """Return list of {title, href, date} sorted newest first, within last 12 months."""
    await page.goto(MEMBERS_URL, timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(2, 4))

    links = await page.eval_on_selector_all(
        "a[href*='premium-20']",
        "els => els.map(e => ({text: e.innerText.trim(), href: e.href}))"
    )

    articles = []
    for link in links:
        date = parse_article_date(link["href"])
        if date and date >= CUTOFF_DATE:
            # Clean title (remove "Month DD, YYYY: " prefix)
            title = re.sub(r"^[A-Za-z]+ \d+, \d{4}:\s*", "", link["text"]).strip()
            if not title:
                title = link["text"].strip()
            articles.append({"title": title, "href": link["href"], "date": date})

    # Sort newest first, deduplicate
    seen = set()
    unique = []
    for a in sorted(articles, key=lambda x: x["date"], reverse=True):
        if a["href"] not in seen:
            seen.add(a["href"])
            unique.append(a)

    return unique


async def main(limit: int):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await login(page)

        print(f"\nFinding articles from the last 12 months...")
        articles = await get_article_links(page)
        print(f"Found {len(articles)} articles in range, scraping latest {limit}:")
        for a in articles[:limit]:
            print(f"  {a['date'].strftime('%Y-%m-%d')} — {a['title']}")

        print(f"\nStarting download (8-20s delay between articles)...")
        saved = []
        for i, article in enumerate(articles[:limit]):
            print(f"\n[{i+1}/{min(limit, len(articles))}] {article['title']}")
            fname = await scrape_article(page, article["href"], article["title"], article["date"])
            if fname:
                saved.append(fname)
            if i < limit - 1:
                await human_delay(8, 20)

        print(f"\n✓ Done. {len(saved)} articles saved to {OUTPUT_DIR}")
        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    limit = 1000 if args.all else args.limit
    asyncio.run(main(limit))
