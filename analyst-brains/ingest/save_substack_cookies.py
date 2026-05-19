"""
One-time setup: opens a visible browser so you can log into Substack manually.
Saves cookies to ~/.substack_cookies.json for use by the scraper.

Usage:
    python save_substack_cookies.py
    (log in, then press Enter in terminal)
"""
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

COOKIES_FILE = Path.home() / ".substack_cookies.json"


async def save_cookies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("Opening Substack sign-in page...")
        await page.goto("https://substack.com/sign-in", wait_until="domcontentloaded")

        print("\n>>> Log into Substack in the browser window that opened.")
        print(">>> Once you're fully logged in, come back here and press Enter.")
        input()

        cookies = await context.cookies()
        COOKIES_FILE.write_text(json.dumps(cookies, indent=2))
        print(f"✓ Saved {len(cookies)} cookies to {COOKIES_FILE}")

        await browser.close()


asyncio.run(save_cookies())
