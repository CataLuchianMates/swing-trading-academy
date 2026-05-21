import base64
import os
import threading
import time
from pathlib import Path

import anthropic
import extra_streamlit_components as stx
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

load_dotenv()

BRAINS_DIR = Path(__file__).parent
PROJECT_ROOT = BRAINS_DIR.parent
WIKI_DIR = PROJECT_ROOT / "wiki"
PERSONAS_DIR = BRAINS_DIR / "personas"

ANALYSTS = {
    "Lyn Alden": "lyn-alden",
    "Phil": "phil",
    "Marlin Capital": "marlin-capital",
}

# ── Models ─────────────────────────────────────────────────────────────────────

MODELS = {
    "Auto":             None,   # routes based on content
    "Gemini 2.0 Flash": "google/gemini-2.0-flash-001",
    "DeepSeek V3":      "deepseek/deepseek-chat-v3-0324",
    "Claude Sonnet 4":  "anthropic/claude-sonnet-4",
}

MODEL_CLAUDE    = "claude-sonnet-4-20250514"
MODEL_GEMINI    = "google/gemini-2.0-flash-001"
MODEL_DEEPSEEK  = "deepseek/deepseek-chat-v3-0324"
MODEL_CLAUDE_OR = "anthropic/claude-sonnet-4"   # via OpenRouter


def pick_model(selected_model: str, has_image: bool) -> str:
    """Return the OpenRouter model string to use."""
    if selected_model == "Auto":
        return MODEL_GEMINI if has_image else MODEL_DEEPSEEK
    return MODELS[selected_model]


def is_native_claude(model_str: str, api_key: str) -> bool:
    """Only use native Anthropic SDK if we have an API key AND it's a Claude model."""
    return bool(api_key) and model_str and "anthropic" in model_str


def get_openrouter_client():
    key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")
    if not key:
        return None
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
    )


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


def load_article_index(analyst_slug: str) -> str:
    """Load the pre-built scraped-index.md for an analyst (titles + teasers only)."""
    index_path = PROJECT_ROOT / "investment_research" / analyst_slug / "scraped" / "scraped-index.md"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return ""


def retrieve_articles(analyst_slug: str, question: str, or_client) -> tuple[list[str], list[str]]:
    """
    Pass 1 — cheap Gemini Flash call: reads the article index and returns
    the slugs of the most relevant articles (up to 5).
    Returns (slugs, titles_for_display).
    """
    index = load_article_index(analyst_slug)
    if not index or not or_client:
        return [], []

    system = (
        "You are an article retrieval assistant. "
        "Given the article index below, identify up to 5 articles most relevant to the user's question. "
        "Return ONLY valid JSON in this exact format, no other text: "
        '{"slugs": ["slug1", "slug2"]}'
    )
    try:
        resp = or_client.chat.completions.create(
            model=MODEL_GEMINI,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Index:\n{index}\n\nQuestion: {question}"},
            ],
            max_tokens=200,
            temperature=0,
        )
        import json, re as _re
        raw = resp.choices[0].message.content or ""
        # Extract JSON even if model adds extra text
        match = _re.search(r'\{.*\}', raw, _re.DOTALL)
        slugs = json.loads(match.group())["slugs"] if match else []
    except Exception:
        slugs = []

    # Load titles for display from the index
    titles = []
    for slug in slugs:
        for line in index.splitlines():
            if f"| {slug} |" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    titles.append(f"{parts[1]} — {parts[3]}")
                break

    return slugs, titles


def load_articles_by_slugs(analyst_slug: str, slugs: list[str]) -> dict[str, str]:
    """Load full article content for given slugs."""
    scraped_path = PROJECT_ROOT / "investment_research" / analyst_slug / "scraped"
    articles = {}
    for slug in slugs:
        f = scraped_path / f"{slug}.md"
        if f.exists():
            articles[slug] = f.read_text(encoding="utf-8")
    return articles


def load_persona(analyst_slug: str) -> str:
    persona_file = PERSONAS_DIR / f"{analyst_slug}.md"
    if persona_file.exists():
        return persona_file.read_text(encoding="utf-8")
    return f"You are {analyst_slug.replace('-', ' ').title()}, a financial analyst."


def build_system_prompt(
    analyst_slug: str,
    wiki_pages: dict[str, str],
    journal_entries: list,
    retrieved_articles: dict[str, str] | None = None,
) -> str:
    persona = load_persona(analyst_slug)

    wiki_section = "\n\n---\n\n".join(
        f"## {name.replace('-', ' ').title()}\n\n{content}"
        for name, content in wiki_pages.items()
    ) if wiki_pages else "*(No wiki pages available yet.)*"

    journal_section = "\n\n".join(
        f"**{e['label']}** ({e['created_at'][:10]})\n{e['content']}"
        for e in reversed(journal_entries)
    ) if journal_entries else "*(No saved insights yet.)*"

    articles_section = ""
    if retrieved_articles:
        articles_section = (
            "\n\n---\n\n"
            "# Retrieved Articles\n\n"
            "IMPORTANT: The following articles from your newsletter archive are provided in full below. "
            "They are part of your knowledge base. Answer questions about them directly — "
            "do NOT say you cannot access them or that they are private. Read them and cite specific details.\n\n"
        )
        articles_section += "\n\n---\n\n".join(
            f"### Article: {slug}\n\n{content}"
            for slug, content in retrieved_articles.items()
        )

    return f"""{persona}

IMPORTANT: Always respond in English only. Never use Chinese, Japanese, Korean, or any other non-English characters or words under any circumstances.

---

# Your Research Notes (Wiki)

{wiki_section}

---

# User's Saved Insights

These are insights the user has specifically chosen to save from past conversations. Reference them when relevant.

{journal_section}
{articles_section}"""


# ── Streaming ──────────────────────────────────────────────────────────────────

def stream_via_openrouter(or_client, model: str, system_prompt: str, messages: list, result: dict, key: str):
    """Stream response via OpenRouter (Gemini, DeepSeek, Claude-via-OR)."""
    full = ""
    or_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
        for m in messages
    ]
    with or_client.chat.completions.create(
        model=model,
        max_tokens=2048,
        messages=or_messages,
        stream=True,
    ) as stream:
        for chunk in stream:
            text = chunk.choices[0].delta.content or ""
            full += text
            result[key] = full
    result[key] = full


def stream_via_anthropic(api_key: str, system_prompt: str, messages: list, result: dict, key: str):
    """Stream response via native Anthropic SDK (prompt caching enabled)."""
    client = anthropic.Anthropic(api_key=api_key)
    full = ""
    with client.messages.stream(
        model=MODEL_CLAUDE,
        max_tokens=2048,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            full += text
            result[key] = full
    result[key] = full


def stream_response(api_key: str, system_prompt: str, messages: list, result: dict, key: str,
                    model: str = None, or_client=None):
    """Route to Anthropic or OpenRouter depending on selected model."""
    if model and not is_native_claude(model, None) and or_client:
        stream_via_openrouter(or_client, model, system_prompt, messages, result, key)
    else:
        stream_via_anthropic(api_key, system_prompt, messages, result, key)


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
    or_client = get_openrouter_client()

    if not or_client and not api_key:
        st.error("No API key found. Add OPENROUTER_API_KEY to secrets.")
        st.stop()

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("🧠 Analyst Brains")

        # Brain selector
        st.subheader("Who answers?")
        selected = [name for name in ANALYSTS if st.checkbox(name, value=True, key=f"check_{name}")]

        st.divider()

        # Model selector
        st.subheader("🤖 Model")
        model_labels = {
            "Auto": "⚡ Auto (recommended)",
            "Gemini 2.0 Flash": "🟢 Gemini Flash — fast & cheap",
            "DeepSeek V3": "🔵 DeepSeek V3 — deep analysis",
            "Claude Sonnet 4": "🔴 Claude Sonnet 4 — best quality",
        }
        if not or_client:
            available_models = ["Claude Sonnet 4"]
            st.caption("Add OPENROUTER_API_KEY to unlock cheaper models")
        else:
            available_models = list(MODELS.keys())
        selected_model = st.radio(
            "Model",
            available_models,
            format_func=lambda x: model_labels.get(x, x),
            label_visibility="collapsed",
        )

        st.divider()

        # Session management
        st.subheader("💬 Conversations")
        if st.button("＋ New chat", use_container_width=True):
            new_sid = create_session()
            if new_sid:
                st.session_state.session_id = new_sid
            else:
                st.session_state.pop("session_id", None)
            st.session_state.messages = []
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

    # ── Chat input (with image attachment via paperclip icon) ─────────────────
    chat_input = st.chat_input(
        "Ask your brains anything... (📎 to attach a chart)",
        accept_file=True,
        file_type=["png", "jpg", "jpeg", "webp"],
    )
    if chat_input:
        prompt = chat_input.text or ""
        uploaded_image = chat_input.files[0] if chat_input.files else None

        if not prompt and not uploaded_image:
            st.stop()
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
        if current_title == "New chat" and prompt:
            update_session_title(session_id, prompt[:60])

        # Save + display user message (text only saved to DB)
        display_prompt = prompt or "📎 Image attached"
        save_message(session_id, "user", display_prompt)
        st.session_state.messages.append({"role": "user", "content": display_prompt})
        with st.chat_message("user"):
            if prompt:
                st.markdown(prompt)
            if uploaded_image:
                st.image(uploaded_image, width=300)

        # Resolve model for this message
        has_image = uploaded_image is not None
        active_model = pick_model(selected_model, has_image)
        use_openrouter = or_client and active_model and not is_native_claude(active_model, api_key)

        # Build API message history
        # OpenRouter uses OpenAI format; Anthropic uses its own format
        api_messages = []
        for i, m in enumerate(st.session_state.messages):
            r = "user" if m["role"] == "user" else "assistant"
            is_last_user = (r == "user" and i == len(st.session_state.messages) - 1)
            if is_last_user and uploaded_image:
                uploaded_image.seek(0)
                img_b64 = base64.b64encode(uploaded_image.read()).decode("utf-8")
                media_type = uploaded_image.type or "image/png"
                if use_openrouter:
                    # OpenAI image format
                    content = [{"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{img_b64}"}}]
                    if prompt:
                        content.append({"type": "text", "text": prompt})
                else:
                    # Anthropic image format
                    content = [{"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_b64}}]
                    if prompt:
                        content.append({"type": "text", "text": prompt})
                api_messages.append({"role": "user", "content": content})
            else:
                api_messages.append({"role": r, "content": m["content"]})

        if len(selected) == 1:
            name = selected[0]
            slug = ANALYSTS[name]
            wiki_pages = load_wiki(slug)
            journal = load_journal(slug)

            # Pass 1 — retrieve relevant articles from index (only for text questions)
            retrieved_articles = {}
            source_titles = []
            if prompt and or_client and load_article_index(slug):
                with st.spinner("🔍 Finding relevant articles…"):
                    slugs, source_titles = retrieve_articles(slug, prompt, or_client)
                    retrieved_articles = load_articles_by_slugs(slug, slugs)

            system_prompt = build_system_prompt(slug, wiki_pages, journal, retrieved_articles)

            with st.chat_message("assistant"):
                model_tag = f" *({selected_model})*" if selected_model != "Auto" else ""
                st.markdown(f"**{name}**{model_tag}")
                placeholder = st.empty()
                full = ""

                if use_openrouter:
                    or_messages = [{"role": "system", "content": system_prompt}] + api_messages
                    with or_client.chat.completions.create(
                        model=active_model, max_tokens=2048,
                        messages=or_messages, stream=True,
                    ) as stream:
                        for chunk in stream:
                            text = chunk.choices[0].delta.content or ""
                            full += text
                            placeholder.markdown(full + "▌")
                else:
                    anthropic_client = anthropic.Anthropic(api_key=api_key)
                    with anthropic_client.messages.stream(
                        model=MODEL_CLAUDE, max_tokens=2048,
                        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
                        messages=api_messages,
                    ) as stream:
                        for text in stream.text_stream:
                            full += text
                            placeholder.markdown(full + "▌")
                placeholder.markdown(full)

                # Show which articles were retrieved as sources
                if source_titles:
                    with st.expander("📰 Articles retrieved", expanded=False):
                        for t in source_titles:
                            st.markdown(f"- {t}")

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
                    kwargs={"model": active_model, "or_client": or_client if use_openrouter else None},
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
