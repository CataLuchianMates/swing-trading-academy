"""
Marlin Capital Substack scraper.
Saves posts as markdown with frontmatter to investment_research/marlin-capital/scraped/
Filename format: YYMMDD-title.md

Usage:
    python scraper_marlin.py              # scrape posts since Dec 1 2024
    python scraper_marlin.py --limit 10   # scrape latest N posts
"""
import argparse
import asyncio
import json
import random
import re
from datetime import datetime
from pathlib import Path

from markdownify import markdownify
from playwright.async_api import async_playwright

ARCHIVE_URL = "https://marlincapital.substack.com/archive"
CUTOFF_DATE = datetime(2024, 12, 1)
COOKIES_FILE = Path.home() / ".substack_cookies.json"

OUTPUT_DIR = Path(__file__).parent.parent.parent / "investment_research" / "marlin-capital" / "scraped"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def human_delay(min_s=8, max_s=20):
    delay = random.uniform(min_s, max_s)
    print(f"  (waiting {delay:.1f}s...)")
    await asyncio.sleep(delay)


async def load_cookies(context):
    if not COOKIES_FILE.exists():
        raise RuntimeError(
            f"No saved cookies found at {COOKIES_FILE}.\n"
            "Run save_substack_cookies.py first to log in manually and save your session."
        )
    cookies = json.loads(COOKIES_FILE.read_text())
    await context.add_cookies(cookies)
    print(f"✓ Loaded {len(cookies)} cookies from {COOKIES_FILE}")


async def get_archive_posts(page) -> list[dict]:
    """Scrape archive page for all posts since CUTOFF_DATE."""
    print(f"\nLoading archive...")
    await page.goto(ARCHIVE_URL, timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(3, 5))

    posts = []
    page_num = 0

    while True:
        page_num += 1
        # Extract post links + dates from current view
        items = await page.eval_on_selector_all(
            "a[href*='/p/']",
            """els => els.map(e => {
                const container = e.closest('div') || e.parentElement;
                const dateEl = container?.querySelector('time') || document.querySelector('time');
                return {
                    href: e.href,
                    title: e.innerText.trim(),
                    datetime: e.closest('[data-testid]')?.querySelector('time')?.getAttribute('datetime') || ''
                }
            })"""
        )

        # Also grab all time elements with nearby links
        all_posts = await page.eval_on_selector_all(
            "[href*='/p/']",
            """els => [...new Set(els.map(e => e.href))].map(href => {
                const el = document.querySelector(`[href="${href}"]`);
                const section = el?.closest('div[class]') || el?.parentElement?.parentElement;
                const time = section?.querySelector('time');
                return {
                    href: href,
                    title: el?.innerText?.trim() || '',
                    datetime: time?.getAttribute('datetime') || ''
                }
            })"""
        )

        stop = False
        for post in all_posts:
            if not post["href"] or not post["title"]:
                continue
            if "/p/" not in post["href"]:
                continue

            # Parse date from datetime attr or URL
            date = None
            if post["datetime"]:
                try:
                    date = datetime.fromisoformat(post["datetime"][:10])
                except:
                    pass

            posts.append({"href": post["href"], "title": post["title"], "date": date})

            if date and date < CUTOFF_DATE:
                stop = True

        # Try to load more / scroll
        if stop:
            break

        # Try clicking "Load more" or scrolling
        try:
            load_more = await page.query_selector('button:has-text("Load more"), a:has-text("Load more")')
            if load_more:
                await load_more.click()
                await asyncio.sleep(random.uniform(2, 4))
            else:
                # Scroll to bottom to trigger infinite scroll
                prev_height = await page.evaluate("document.body.scrollHeight")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(3)
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == prev_height:
                    break  # No more content
        except:
            break

        if page_num > 20:  # Safety limit
            break

    # Deduplicate + filter by date
    seen = set()
    filtered = []
    for p in posts:
        if p["href"] in seen or not p["title"]:
            continue
        seen.add(p["href"])
        if p["date"] is None or p["date"] >= CUTOFF_DATE:
            filtered.append(p)

    return sorted(filtered, key=lambda x: x["date"] or datetime.min, reverse=True)


def make_filename(title: str, date: datetime) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    slug = re.sub(r"-+", "-", slug)[:60]
    date_str = date.strftime("%y%m%d") if date else "000000"
    return f"{date_str}-{slug}.md"


def extract_content(html: str, title: str, date: datetime, url: str) -> str:
    md = markdownify(html, heading_style="ATX", strip=["script", "style", "nav", "footer", "iframe"])
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    date_str = date.strftime("%Y-%m-%d") if date else "unknown"
    return f"""---
title: "{title}"
date: "{date_str}"
source_url: "{url}"
analyst: "David Marlin"
publication: "Marlin Capital"
type: "substack_newsletter"
---

# {title}

{md}
"""


async def scrape_post(page, post: dict) -> str | None:
    filename = make_filename(post["title"], post["date"])
    output_path = OUTPUT_DIR / filename

    if output_path.exists():
        print(f"  ✓ Already saved: {filename}")
        return filename

    print(f"  Fetching: {post['title']}")
    await page.goto(post["href"], timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(3, 5))

    # Get date from JSON-LD structured data
    try:
        json_ld_texts = await page.eval_on_selector_all(
            'script[type="application/ld+json"]',
            "els => els.map(e => e.innerText)"
        )
        for raw in json_ld_texts:
            data = json.loads(raw)
            dp = data.get("datePublished") or data.get("dateModified")
            if dp:
                post["date"] = datetime.fromisoformat(dp[:10])
                filename = make_filename(post["title"], post["date"])
                output_path = OUTPUT_DIR / filename
                if output_path.exists():
                    print(f"  ✓ Already saved: {filename}")
                    return filename
                break
    except Exception:
        pass

    # Extract article content
    try:
        content_html = await page.eval_on_selector(
            "article, .body, .post-content, div.available-content",
            "el => el.innerHTML"
        )
    except:
        content_html = await page.eval_on_selector("body", "el => el.innerHTML")

    md_content = extract_content(content_html, post["title"], post["date"], post["href"])
    output_path.write_text(md_content, encoding="utf-8")
    print(f"  ✓ Saved: {filename} ({len(md_content)} chars)")
    return filename


async def main(limit: int):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        await load_cookies(context)
        page = await context.new_page()

        await human_delay(3, 5)
        posts = await get_archive_posts(page)
        posts = posts[:limit]

        print(f"\nFound {len(posts)} posts to scrape (since {CUTOFF_DATE.strftime('%b %Y')}):")
        for post in posts[:10]:
            date_str = post["date"].strftime("%Y-%m-%d") if post["date"] else "unknown"
            print(f"  {date_str} — {post['title'][:60]}")
        if len(posts) > 10:
            print(f"  ... and {len(posts)-10} more")

        print(f"\nStarting download (8-20s delay between posts)...")
        saved = []
        for i, post in enumerate(posts):
            print(f"\n[{i+1}/{len(posts)}] {post['title'][:60]}")
            fname = await scrape_post(page, post)
            if fname:
                saved.append(fname)
            if i < len(posts) - 1:
                await human_delay(8, 20)

        print(f"\n✓ Done. {len(saved)} posts saved to {OUTPUT_DIR}")
        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    asyncio.run(main(args.limit))
