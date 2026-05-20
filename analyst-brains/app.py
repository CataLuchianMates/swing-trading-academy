import base64
import os
import threading
import time
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


# ── Sessions ───────────────────────────────────────────────────────────────────

def load_sessions() -> list:
    db = get_supabase()
    if not db:
        return []
    try:
        res = db.table("sessions").select("id, title, created_at").order("updated_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []


def create_session(title: str = "New chat") -> int | None:
    db = get_supabase()
    if not db:
        return None
    try:
        res = db.table("sessions").insert({"title": title}).execute()
        return res.data[0]["id"]
    except Exception:
        return None


def update_session_title(session_id: int, title: str):
    db = get_supabase()
    if not db:
        return
    try:
        db.table("sessions").update({"title": title, "updated_at": "now()"}).eq("id", session_id).execute()
    except Exception:
        pass


def touch_session(session_id: int):
    db = get_supabase()
    if not db:
        return
    try:
        db.table("sessions").update({"updated_at": "now()"}).eq("id", session_id).execute()
    except Exception:
        pass


def delete_session(session_id: int):
    db = get_supabase()
    if not db:
        return
    try:
        db.table("sessions").delete().eq("id", session_id).execute()
    except Exception:
        pass


# ── Messages ───────────────────────────────────────────────────────────────────

def load_messages(session_id: int) -> list:
    db = get_supabase()
    if not db:
        return []
    try:
        res = db.table("messages").select("role, content, created_at").eq("session_id", session_id).order("created_at").execute()
        return res.data or []
    except Exception:
        return []


def save_message(session_id: int, role: str, content: str):
    """role: 'user', 'lyn-alden', 'phil'"""
    db = get_supabase()
    if not db:
        return
    try:
        db.table("messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content,
        }).execute()
        touch_session(session_id)
    except Exception:
        pass


# ── Journal ────────────────────────────────────────────────────────────────────

def load_journal(analyst_slug: str) -> list:
    db = get_supabase()
    if not db:
        return []
    try:
        res = db.table("journal").select("*").eq("analyst_slug", analyst_slug).order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []


def save_journal_entry(analyst_slug: str, label: str, content: str):
    db = get_supabase()
    if not db:
        return
    try:
        # Check if label already exists
        res = db.table("journal").select("id, content").eq("analyst_slug", analyst_slug).eq("label", label).execute()
        from datetime import date
        today = date.today().isoformat()
        if res.data:
            # Append to existing entry
            existing = res.data[0]
            updated = f"{existing['content']}\n\n---\n\n**[{today}]**\n{content}"
            db.table("journal").update({
                "content": updated,
                "created_at": "now()",
            }).eq("id", existing["id"]).execute()
        else:
            # Create new entry
            db.table("journal").insert({
                "analyst_slug": analyst_slug,
                "label": label,
                "content": f"**[{today}]**\n{content}",
            }).execute()
    except Exception:
        pass


def delete_journal_entry(entry_id: int):
    db = get_supabase()
    if not db:
        return
    try:
        db.table("journal").delete().eq("id", entry_id).execute()
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

    wiki_section = "\n\n---\n\n".join(
        f"## {name.replace('-', ' ').title()}\n\n{content}"
        for name, content in wiki_pages.items()
    ) if wiki_pages else "*(No wiki pages available yet.)*"

    journal_section = "\n\n".join(
        f"**{e['label']}** ({e['created_at'][:10]})\n{e['content']}"
        for e in reversed(journal_entries)
    ) if journal_entries else "*(No saved insights yet.)*"

    return f"""{persona}

---

# Your Research Notes

{wiki_section}

---

# User's Saved Insights

These are insights the user has specifically chosen to save from past conversations. Reference them when relevant.

{journal_section}
"""


# ── Streaming ──────────────────────────────────────────────────────────────────

def stream_response(api_key: str, system_prompt: str, messages: list, result: dict, key: str):
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
            result[key] = full
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

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("🧠 Analyst Brains")

        # Brain selector
        st.subheader("Who answers?")
        selected = [name for name in ANALYSTS if st.checkbox(name, value=True, key=f"check_{name}")]

        st.divider()

        # Session management
        st.subheader("💬 Conversations")
        if st.button("＋ New chat", use_container_width=True):
            st.session_state.pop("session_id", None)
            st.session_state.pop("messages", None)
            st.rerun()

        sessions = load_sessions()
        for s in sessions:
            col1, col2 = st.columns([5, 1])
            label = s["title"][:35] + ("…" if len(s["title"]) > 35 else "")
            date = s["created_at"][:10]
            active = st.session_state.get("session_id") == s["id"]
            with col1:
                if st.button(f"{'▶ ' if active else ''}{label}\n{date}", key=f"sess_{s['id']}", use_container_width=True):
                    st.session_state.session_id = s["id"]
                    st.session_state.pop("messages", None)
                    st.rerun()
            with col2:
                if st.button("🗑", key=f"del_sess_{s['id']}"):
                    delete_session(s["id"])
                    if st.session_state.get("session_id") == s["id"]:
                        st.session_state.pop("session_id", None)
                        st.session_state.pop("messages", None)
                    st.rerun()

        st.divider()

        # Journal
        active_slug = ANALYSTS[selected[0]] if selected else "lyn-alden"
        journal_entries = load_journal(active_slug)

        st.subheader("📓 Saved Insights")
        if journal_entries:
            for entry in journal_entries:
                with st.expander(f"**{entry['label']}** — {entry['created_at'][:10]}"):
                    st.markdown(entry["content"])
                    if st.button("🗑 Delete", key=f"del_j_{entry['id']}"):
                        delete_journal_entry(entry["id"])
                        st.rerun()
        else:
            st.caption("Nothing saved yet.")

    # ── Main area ──────────────────────────────────────────────────────────────
    st.title("🧠 Analyst Brains")

    # Ensure we have a session
    if "session_id" not in st.session_state:
        # Auto-load the most recent session if one exists
        if sessions:
            st.session_state.session_id = sessions[0]["id"]
        else:
            sid = create_session()
            if sid:
                st.session_state.session_id = sid

    session_id = st.session_state.get("session_id")

    # Load messages for current session
    if "messages" not in st.session_state:
        st.session_state.messages = load_messages(session_id) if session_id else []

    # Display messages
    for msg in st.session_state.messages:
        role = msg["role"]
        if role == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            # role is analyst slug e.g. "lyn-alden"
            display_name = next((k for k, v in ANALYSTS.items() if v == role), role)
            with st.chat_message("assistant"):
                st.markdown(f"**{display_name}**")
                st.markdown(msg["content"])

    # Save to journal
    with st.expander("📌 Save insight to journal"):
        brain_for_journal = st.selectbox("Save under", list(ANALYSTS.keys()), key="jbrain")
        existing_labels = [e["label"] for e in load_journal(ANALYSTS[brain_for_journal])]
        label_options = existing_labels + ["＋ New label..."]
        chosen = st.selectbox("Label", label_options, index=len(label_options) - 1, key="jlabel_select")
        if chosen == "＋ New label...":
            label = st.text_input("New label name", placeholder="e.g. EM rotation trigger", key="jlabel_new")
        else:
            label = chosen
        content = st.text_area("Paste text to save", height=100, key="jcontent")
        if st.button("Save to journal"):
            if label.strip() and content.strip():
                save_journal_entry(ANALYSTS[brain_for_journal], label.strip(), content.strip())
                st.success("Saved!")
                st.rerun()
            else:
                st.warning("Add a label and content first.")

    # ── Image upload ───────────────────────────────────────────────────────────
    uploaded_image = st.file_uploader(
        "📎 Attach a chart or screenshot (optional)",
        type=["png", "jpg", "jpeg", "webp"],
        key="img_upload",
        label_visibility="collapsed",
    )
    if uploaded_image:
        st.image(uploaded_image, caption="Attached", width=300)

    # ── Chat input ─────────────────────────────────────────────────────────────
    if prompt := st.chat_input("Ask your brains anything..."):
        if not selected:
            st.warning("Select at least one brain in the sidebar.")
            st.stop()

        # Create session if needed
        if not session_id:
            session_id = create_session()
            st.session_state.session_id = session_id
            st.session_state.messages = []

        # Auto-title session from first message
        current_sessions = load_sessions()
        current_title = next((s["title"] for s in current_sessions if s["id"] == session_id), "New chat")
        if current_title == "New chat":
            update_session_title(session_id, prompt[:60])

        # Save + display user message
        save_message(session_id, "user", prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            if uploaded_image:
                st.image(uploaded_image, width=300)

        # Build API message history (user/assistant only, normalized roles)
        # Images are session-only — not persisted to Supabase
        api_messages = []
        for i, m in enumerate(st.session_state.messages):
            r = "user" if m["role"] == "user" else "assistant"
            # Attach image to the last user message only
            is_last_user = (r == "user" and i == len(st.session_state.messages) - 1)
            if is_last_user and uploaded_image:
                uploaded_image.seek(0)
                img_bytes = uploaded_image.read()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                media_type = uploaded_image.type or "image/png"
                api_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                })
            else:
                api_messages.append({"role": r, "content": m["content"]})

        if len(selected) == 1:
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

            save_message(session_id, slug, full)
            st.session_state.messages.append({"role": slug, "content": full})

        else:
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

            cols = st.columns(len(selected))
            placeholders = {}
            for i, name in enumerate(selected):
                with cols[i]:
                    st.markdown(f"**{name}**")
                    placeholders[name] = st.empty()

            while any(t.is_alive() for t in threads):
                for name in selected:
                    placeholders[name].markdown(results[name] + "▌")
                time.sleep(0.1)

            for name in selected:
                placeholders[name].markdown(results[name])
                slug = ANALYSTS[name]
                save_message(session_id, slug, results[name])
                st.session_state.messages.append({"role": slug, "content": results[name]})


if __name__ == "__main__":
    main()
