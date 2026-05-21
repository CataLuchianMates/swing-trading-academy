"""
Build a scraped-index.md for each analyst's scraped/ folder.

For each article: extracts title, date, slug, and a ~200-char plain-text
teaser from the body (used by Pass 1 retrieval to find relevant articles).

Run after scraping new articles:
    python analyst-brains/ingest/build_index.py
"""

import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESEARCH_ROOT = PROJECT_ROOT / "investment_research"

ANALYSTS = {
    "marlin-capital": "Marlin Capital",
    "lyn-alden": "Lyn Alden",
}


def strip_markdown(text: str) -> str:
    """Remove markdown noise to get clean plain text for the teaser."""
    # Remove image tags
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Remove links but keep link text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove markdown headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r"\*{1,3}([^\*]+)\*{1,3}", r"\1", text)
    # Remove horizontal rules
    text = re.sub(r"^[-*]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and return (meta_dict, body)."""
    meta = {}
    if not content.startswith("---"):
        return meta, content
    end = content.find("---", 3)
    if end == -1:
        return meta, content
    fm = content[3:end]
    for line in fm.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"')
    body = content[end + 3:].strip()
    return meta, body


def extract_teaser(body: str, max_chars: int = 220) -> str:
    """Get the first meaningful plain-text snippet from the body."""
    clean = strip_markdown(body)
    lines = [l.strip() for l in clean.splitlines() if len(l.strip()) > 30]
    # Skip generic openers
    skip_starts = ("dear ", "hello ", "hi ", "marlin capital reader", "lyn alden reader")
    lines = [l for l in lines if not l.lower().startswith(skip_starts)]
    teaser = " ".join(lines)[:max_chars]
    # Cut at last full word
    if len(teaser) == max_chars:
        teaser = teaser.rsplit(" ", 1)[0] + "…"
    return teaser


def build_index_for_analyst(analyst_slug: str, analyst_name: str):
    scraped_path = RESEARCH_ROOT / analyst_slug / "scraped"
    if not scraped_path.exists():
        print(f"  No scraped/ folder for {analyst_name}, skipping.")
        return

    articles = sorted(
        [f for f in scraped_path.glob("*.md") if "comments" not in f.name],
        key=lambda f: f.name,
    )

    rows = []
    for f in articles:
        content = f.read_text(encoding="utf-8")
        meta, body = extract_frontmatter(content)
        date = meta.get("date", "unknown")
        title = meta.get("title", f.stem)
        slug = f.stem
        teaser = extract_teaser(body)
        rows.append((date, slug, title, teaser))

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Article Index — {analyst_name}",
        f"_Last updated: {now} | {len(rows)} articles_",
        "",
        "| Date | Slug | Title | Summary |",
        "|------|------|-------|---------|",
    ]
    for date, slug, title, teaser in rows:
        # Escape pipes in content
        title_esc = title.replace("|", "/")
        teaser_esc = teaser.replace("|", "/").replace("\n", " ")
        lines.append(f"| {date} | {slug} | {title_esc} | {teaser_esc} |")

    index_path = scraped_path / "scraped-index.md"
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  ✓ {analyst_name}: {len(rows)} articles → {index_path.relative_to(PROJECT_ROOT)}")


def main():
    print("Building article indexes...")
    for slug, name in ANALYSTS.items():
        build_index_for_analyst(slug, name)
    print("Done.")


if __name__ == "__main__":
    main()
