"""
Marlin Capital Substack scraper — uses saved cookies, no browser automation.
Hits the Substack API directly with requests. No login, no CAPTCHA, no lockouts.

Usage:
    python scraper_marlin.py              # scrape all posts since Dec 2024
    python scraper_marlin.py --limit 5    # scrape latest N posts
    python scraper_marlin.py --since 2024-01-01

Refresh cookies: export from Cookie-Editor on marlincapital.substack.com
and save to analyst-brains/ingest/substack_cookies.json
"""
import argparse
import json
import re
import time
import random
from datetime import datetime
from pathlib import Path

import requests
from markdownify import markdownify

PUBLICATION = "marlincapital"
BASE_URL = f"https://{PUBLICATION}.substack.com"
COOKIES_FILE = Path(__file__).parent / "substack_cookies.json"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "investment_research" / "marlin-capital" / "scraped"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CUTOFF_DATE = datetime(2024, 12, 1)


def load_cookies() -> dict:
    if not COOKIES_FILE.exists():
        raise FileNotFoundError(f"No cookies file at {COOKIES_FILE}. Export from Cookie-Editor first.")
    raw = json.loads(COOKIES_FILE.read_text())
    return {c["name"]: c["value"] for c in raw}


def get_session(cookies: dict) -> requests.Session:
    s = requests.Session()
    s.cookies.update(cookies)
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": BASE_URL,
    })
    return s


def get_all_posts(session: requests.Session, cutoff: datetime) -> list[dict]:
    """Fetch post list from Substack API."""
    posts = []
    offset = 0
    limit = 50

    print(f"Fetching post list from API...")
    while True:
        url = f"{BASE_URL}/api/v1/posts?limit={limit}&offset={offset}&sort=new"
        res = session.get(url, timeout=30)
        if res.status_code != 200:
            print(f"  API error {res.status_code} — cookies may be expired")
            break

        batch = res.json()
        if not batch:
            break

        for post in batch:
            published = post.get("post_date") or post.get("updated_at", "")
            try:
                date = datetime.fromisoformat(published[:10])
            except Exception:
                date = None

            posts.append({
                "id": post.get("id"),
                "slug": post.get("slug"),
                "title": post.get("title", "Untitled"),
                "date": date,
                "url": f"{BASE_URL}/p/{post.get('slug')}",
            })

            if date and date < cutoff:
                return posts

        offset += limit
        time.sleep(random.uniform(1, 2))

        if len(batch) < limit:
            break

    return posts


def get_post_content(session: requests.Session, slug: str) -> tuple[str | None, int | None]:
    """Fetch full post HTML via API. Returns (html, post_id)."""
    url = f"{BASE_URL}/api/v1/posts/{slug}"
    res = session.get(url, timeout=30)
    if res.status_code != 200:
        return None, None
    data = res.json()
    html = data.get("body_html") or data.get("truncated_body_text")
    return html, data.get("id")


def get_marlin_comments(session: requests.Session, post_id: int) -> str:
    """Fetch David Marlin's own replies from the comments section."""
    url = f"{BASE_URL}/api/v1/post/{post_id}/comments?all_comments=true&sort=top_first"
    res = session.get(url, timeout=30)
    if res.status_code != 200:
        return ""

    comments = res.json().get("comments", [])
    marlin_replies = []

    for comment in comments:
        # Check David's top-level comments
        if (comment.get("name") or "").lower() in ("david marlin", "david"):
            body = (comment.get("body") or "").strip()
            if body:
                marlin_replies.append(f"**David Marlin:** {body}")

        # Check David's replies inside each comment thread
        for child in comment.get("children", []):
            if (child.get("name") or "").lower() in ("david marlin", "david"):
                body = (child.get("body") or "").strip()
                question = (comment.get("body") or "").strip()
                if body:
                    if question:
                        marlin_replies.append(f"**Q:** {question}\n\n**David Marlin:** {body}")
                    else:
                        marlin_replies.append(f"**David Marlin:** {body}")

    if not marlin_replies:
        return ""

    return "\n\n---\n\n## David Marlin Q&A (Comments)\n\n" + "\n\n---\n\n".join(marlin_replies)


def make_filename(title: str, date: datetime) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    slug = re.sub(r"-+", "-", slug)[:60]
    date_str = date.strftime("%y%m%d") if date else "000000"
    return f"{date_str}-{slug}.md"


def make_markdown(html: str, title: str, date: datetime, url: str) -> str:
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


def make_comments_markdown(comments_md: str, title: str, date: datetime, url: str) -> str:
    date_str = date.strftime("%Y-%m-%d") if date else "unknown"
    return f"""---
title: "{title} — Comments"
date: "{date_str}"
source_url: "{url}/comments"
analyst: "David Marlin"
publication: "Marlin Capital"
type: "substack_comments"
---

# {title} — David Marlin Q&A

{comments_md}
"""


def main(limit: int, cutoff: datetime):
    cookies = load_cookies()
    session = get_session(cookies)

    # Verify auth
    test = session.get(f"{BASE_URL}/api/v1/subscriber", timeout=10)
    if test.status_code == 200:
        data = test.json()
        print(f"✓ Authenticated as: {data.get('email', 'unknown')}")
    else:
        print(f"⚠ Auth check returned {test.status_code} — proceeding anyway")

    posts = get_all_posts(session, cutoff)
    posts = [p for p in posts if p["date"] is None or p["date"] >= cutoff]
    posts = sorted(posts, key=lambda x: x["date"] or datetime.min, reverse=True)
    posts = posts[:limit]

    print(f"\nFound {len(posts)} posts since {cutoff.strftime('%b %Y')}:")
    for p in posts[:10]:
        date_str = p["date"].strftime("%Y-%m-%d") if p["date"] else "unknown"
        print(f"  {date_str} — {p['title'][:60]}")
    if len(posts) > 10:
        print(f"  ... and {len(posts) - 10} more")

    print(f"\nDownloading...")
    saved = []
    for i, post in enumerate(posts):
        filename = make_filename(post["title"], post["date"])
        output_path = OUTPUT_DIR / filename

        if output_path.exists():
            print(f"[{i+1}/{len(posts)}] ✓ Already saved: {filename}")
            continue

        print(f"[{i+1}/{len(posts)}] Fetching: {post['title'][:60]}")
        html, post_id = get_post_content(session, post["slug"])

        if not html:
            print(f"  ✗ No content returned (may be paywalled without valid subscription)")
            continue

        md = make_markdown(html, post["title"], post["date"], post["url"])
        output_path.write_text(md, encoding="utf-8")
        print(f"  ✓ Saved: {filename} ({len(md):,} chars)")
        saved.append(filename)

        # Fetch and save comments as a separate file
        if post_id:
            comments_md = get_marlin_comments(session, post_id)
            if comments_md:
                comments_filename = filename.replace(".md", "-comments.md")
                comments_path = OUTPUT_DIR / comments_filename
                if not comments_path.exists():
                    comments_content = make_comments_markdown(comments_md, post["title"], post["date"], post["url"])
                    comments_path.write_text(comments_content, encoding="utf-8")
                    print(f"  ✓ Saved comments: {comments_filename}")

        time.sleep(random.uniform(2, 5))

    print(f"\n✓ Done. {len(saved)} new posts saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--since", type=str, default="2024-12-01")
    args = parser.parse_args()
    cutoff = datetime.strptime(args.since, "%Y-%m-%d")
    main(args.limit, cutoff)
