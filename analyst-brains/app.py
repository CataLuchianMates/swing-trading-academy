import os
import threading
from pathlib import Path

import anthropic
import extra_streamlit_components as stx
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

BRAINS_DIR = Path(__file__).parent
PROJECT_ROOT = BRAINS_DIR.parent
WIKI_DIR = PROJECT_ROOT / "wiki"
PERSONAS_DIR = BRAINS_DIR / "personas"

ANALYSTS = {
    "Lyn Alden": "lyn-alden",
    "Phil": "phil",
}

MODEL = "claude-sonnet-4-20250514"


def get_supabase():
    url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


# ── Conversations ──────────────────────────────────────────────────────────────

def load_messages(analyst_slug: str) -> list:
    client = get_supabase()
    if not client:
        return []
    try:
        res = client.table("conversations").select("messages").eq("analyst_slug", analyst_slug).single().execute()
        return res.data["messages"] if res.data else []
    except Exception:
        return []


def save_messages(analyst_slug: str, messages: list):
    client = get_supabase()
    if not client:
        return
    try:
        client.table("conversations").upsert({
            "analyst_slug": analyst_slug,
            "messages": messages,
            "updated_at": "now()",
        }).execute()
    except Exception:
        pass


def clear_messages(analyst_slug: str):
    client = get_supabase()
    if not client:
        return
    try:
        client.table("conversations").upsert({
            "analyst_slug": analyst_slug,
            "messages": [],
            "updated_at": "now()",
        }).execute()
    except Exception:
        pass


# ── Journal ────────────────────────────────────────────────────────────────────

def load_journal(analyst_slug: str) -> list:
    client = get_supabase()
    if not client:
        return []
    try:
        res = client.table("journal").select("*").eq("analyst_slug", analyst_slug).order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []


def save_journal_entry(analyst_slug: str, label: str, content: str):
    client = get_supabase()
    if not client:
        return
    try:
        client.table("journal").insert({
            "analyst_slug": analyst_slug,
            "label": label,
            "content": content,
        }).execute()
    except Exception:
        pass


def delete_journal_entry(entry_id: int):
    client = get_supabase()
    if not client:
        return
    try:
        client.table("journal").delete().eq("id", entry_id).execute()
    except Exception:
        pass


# ── Wiki & persona ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading wiki...")
def load_wiki(analyst_slug: str) -> dict[str, str]:
    wiki_path = WIKI_DIR / analyst_slug
    if not wiki_path.exists():
        return {}
    return {
        md_file.stem: md_file.read_text(encoding="utf-8")
        for md_file in sorted(wiki_path.glob("*.md"))
    }


def load_persona(analyst_slug: str) -> str:
    persona_file = PERSONAS_DIR / f"{analyst_slug}.md"
    if persona_file.exists():
        return persona_file.read_text(encoding="utf-8")
    return f"You are {analyst_slug.replace('-', ' ').title()}, a financial analyst."


def build_system_prompt(analyst_slug: str, wiki_pages: dict[str, str], journal_entries: list) -> str:
    persona = load_persona(analyst_slug)

    if not wiki_pages:
        wiki_section = "*(No wiki pages available yet.)*"
    else:
        wiki_section = "\n\n---\n\n".join(
            f"## {name.replace('-', ' ').title()}\n\n{content}"
            for name, content in wiki_pages.items()
        )

    if journal_entries:
        journal_section = "\n\n".join(
            f"**{e['label']}** ({e['created_at'][:10]})\n{e['content']}"
            for e in reversed(journal_entries)
        )
    else:
        journal_section = "*(No saved insights yet.)*"

    return f"""{persona}

---

# Your Research Notes

{wiki_section}

---

# User's Saved Insights

These are insights the user has specifically chosen to save from past conversations. Reference them when relevant.

{journal_section}
"""


# ── API call ───────────────────────────────────────────────────────────────────

def stream_response(api_key: str, system_prompt: str, messages: list, result: dict, key: str):
    """Run a streaming API call and store the full response in result[key]."""
    client = anthropic.Anthropic(api_key=api_key)
    full = ""
    with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            full += text
            result[key] = full  # update incrementally
    result[key] = full


# ── Auth ───────────────────────────────────────────────────────────────────────

def get_cookie_manager():
    return stx.CookieManager(key="auth_cookies")


def check_password() -> bool:
    cookie_manager = get_cookie_manager()

    if st.session_state.get("authenticated"):
        return True

    if cookie_manager.get("analyst_brain_auth") == "1":
        st.session_state.authenticated = True
        return True

    pwd = st.secrets.get("APP_PASSWORD")
    if not pwd:
        return True

    entered = st.text_input("Password", type="password", key="pw_input")
    if st.button("Enter"):
        if entered == pwd:
            st.session_state.authenticated = True
            cookie_manager.set("analyst_brain_auth", "1", key="set_auth")
            st.rerun()
        else:
            st.error("Incorrect password")
    return False


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Analyst Brains", page_icon="🧠", layout="wide")

    if not check_password():
        st.stop()

    api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not found.")
        st.stop()

    # ── Sidebar ──
    with st.sidebar:
        st.title("🧠 Analyst Brains")

        st.subheader("Who answers?")
        selected = []
        for name in ANALYSTS:
            if st.checkbox(name, value=True, key=f"check_{name}"):
                selected.append(name)

        st.divider()

        # Journal — shown for first selected brain
        active_slug = ANALYSTS[selected[0]] if selected else list(ANALYSTS.values())[0]
        journal_entries = load_journal(active_slug)

        st.subheader("📓 Saved Insights")
        if journal_entries:
            for entry in journal_entries:
                with st.expander(f"**{entry['label']}** — {entry['created_at'][:10]}"):
                    st.markdown(entry["content"])
                    if st.button("🗑 Delete", key=f"del_{entry['id']}"):
                        delete_journal_entry(entry["id"])
                        st.rerun()
        else:
            st.caption("Nothing saved yet.")

        st.divider()

        if st.button("Clear chat"):
            for name in ANALYSTS:
                clear_messages(ANALYSTS[name])
            st.session_state.chat_history = []
            st.rerun()

    # ── Chat history (shared across brains) ──
    if "chat_history" not in st.session_state:
        # Load from first brain as the shared base
        st.session_state.chat_history = load_messages("shared") or []

    st.title("🧠 Analyst Brains")

    # Render existing history
    for entry in st.session_state.chat_history:
        if entry["role"] == "user":
            with st.chat_message("user"):
                st.markdown(entry["content"])
        else:
            # assistant entries have a "brain" key
            brain = entry.get("brain", "Assistant")
            with st.chat_message("assistant"):
                st.markdown(f"**{brain}**")
                st.markdown(entry["content"])

    # Save to journal
    with st.expander("📌 Save insight to journal"):
        label = st.text_input("Label", placeholder="e.g. EM rotation trigger, Bitcoin thesis", key="journal_label")
        content = st.text_area("Paste the text you want to save", height=100, key="journal_content")
        brain_for_journal = st.selectbox("Save under", list(ANALYSTS.keys()), key="journal_brain")
        if st.button("Save to journal"):
            if label.strip() and content.strip():
                save_journal_entry(ANALYSTS[brain_for_journal], label.strip(), content.strip())
                st.success("Saved!")
                st.rerun()
            else:
                st.warning("Add a label and content first.")

    # ── Chat input ──
    if prompt := st.chat_input("Ask your brains anything..."):
        if not selected:
            st.warning("Select at least one brain in the sidebar.")
            st.stop()

        # Show user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build message history for API (user/assistant turns only, no brain metadata)
        api_messages = [
            {"role": e["role"], "content": e["content"]}
            for e in st.session_state.chat_history
        ]

        if len(selected) == 1:
            # ── Single brain — stream directly ──
            name = selected[0]
            slug = ANALYSTS[name]
            wiki_pages = load_wiki(slug)
            journal = load_journal(slug)
            system_prompt = build_system_prompt(slug, wiki_pages, journal)

            with st.chat_message("assistant"):
                st.markdown(f"**{name}**")
                placeholder = st.empty()
                full = ""
                client = anthropic.Anthropic(api_key=api_key)
                with client.messages.stream(
                    model=MODEL,
                    max_tokens=2048,
                    system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
                    messages=api_messages,
                ) as stream:
                    for text in stream.text_stream:
                        full += text
                        placeholder.markdown(full + "▌")
                placeholder.markdown(full)

            st.session_state.chat_history.append({"role": "assistant", "content": full, "brain": name})

        else:
            # ── Multiple brains — run in parallel, display side by side ──
            results = {name: "" for name in selected}
            threads = []

            for name in selected:
                slug = ANALYSTS[name]
                wiki_pages = load_wiki(slug)
                journal = load_journal(slug)
                system_prompt = build_system_prompt(slug, wiki_pages, journal)
                t = threading.Thread(
                    target=stream_response,
                    args=(api_key, system_prompt, api_messages, results, name),
                    daemon=True,
                )
                threads.append(t)
                t.start()

            # Show columns with live-updating placeholders
            cols = st.columns(len(selected))
            placeholders = {}
            for i, name in enumerate(selected):
                with cols[i]:
                    st.markdown(f"**{name}**")
                    placeholders[name] = st.empty()

            # Poll until all threads done
            import time
            while any(t.is_alive() for t in threads):
                for name in selected:
                    placeholders[name].markdown(results[name] + "▌")
                time.sleep(0.1)

            # Final render
            for name in selected:
                placeholders[name].markdown(results[name])
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": results[name],
                    "brain": name,
                })

        # Save shared history
        save_messages("shared", [
            {"role": e["role"], "content": e["content"]}
            for e in st.session_state.chat_history
        ])


if __name__ == "__main__":
    main()
