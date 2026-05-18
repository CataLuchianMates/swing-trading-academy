"""Maps Lyn Alden's members area — finds all newsletter article links."""
import asyncio
import random
from playwright.async_api import async_playwright

LOGIN_URL = "https://www.lynalden.com/login/"
MEMBERS_URL = "https://www.lynalden.com/members/"
EMAIL = "catalin.mates@gmail.com"
PASSWORD = "Vancouver2025!"


async def human_delay(min_s=2, max_s=5):
    await asyncio.sleep(random.uniform(min_s, max_s))


async def login(page):
    await page.goto(LOGIN_URL, timeout=60000, wait_until="domcontentloaded")
    await human_delay(2, 3)
    await page.fill('input[name="rcp_user_login"]', EMAIL)
    await human_delay(1, 2)
    await page.fill('input[name="rcp_user_pass"]', PASSWORD)
    await human_delay(1, 2)
    await page.click('input[id="rcp_login_submit"]')
    await page.wait_for_load_state("domcontentloaded")
    await human_delay(2, 3)
    assert "members" in page.url, f"Login failed, landed on {page.url}"
    print("✓ Logged in")


async def discover():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await login(page)

        # Get all links on members page
        print("\nMembers page links:")
        links = await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({text: e.innerText.trim().slice(0,80), href: e.href}))"
        )
        newsletter_links = []
        for link in links:
            if link["text"]:
                print(f"  {link['text']:<70} {link['href']}")
                if "lynalden.com" in link["href"] and link["href"] not in [
                    "https://www.lynalden.com/",
                    "https://www.lynalden.com/members/",
                    "https://www.lynalden.com/login/",
                    "https://www.lynalden.com/premium/",
                ]:
                    newsletter_links.append(link)

        # Also check if there's a paginated archive
        print("\n\nChecking for newsletter archive pages...")
        for path in [
            "/category/newsletter/",
            "/category/research/",
            "/category/premium/",
            "/premium-research/",
            "/research/",
        ]:
            url = f"https://www.lynalden.com{path}"
            resp = await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            await human_delay(1, 2)
            if resp and resp.status == 200:
                title = await page.title()
                print(f"  ✓ {path} — {title}")
                links = await page.eval_on_selector_all(
                    "a[href]",
                    "els => els.map(e => ({text: e.innerText.trim().slice(0,80), href: e.href}))"
                )
                print(f"    {len(links)} links found")
                for l in links[:20]:
                    if l["text"]:
                        print(f"    {l['text']:<70} {l['href']}")

        await browser.close()


asyncio.run(discover())
