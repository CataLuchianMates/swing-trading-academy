import os
from pathlib import Path

import anthropic
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BRAINS_DIR = Path(__file__).parent
PROJECT_ROOT = BRAINS_DIR.parent
WIKI_DIR = PROJECT_ROOT / "wiki"
PERSONAS_DIR = BRAINS_DIR / "personas"

ANALYSTS = {
    "Lyn Alden": "lyn_alden",
    # Add more: "Marlin Capital": "marlin_capital", "Doomberg": "doomberg"
}

MODEL = "claude-sonnet-4-20250514"


@st.cache_data(show_spinner="Loading wiki...")
def load_wiki(analyst_slug: str) -> dict[str, str]:
    wiki_path = WIKI_DIR / analyst_slug
    if not wiki_path.exists():
        return {}
    pages = {}
    for md_file in sorted(wiki_path.glob("*.md")):
        pages[md_file.stem] = md_file.read_text(encoding="utf-8")
    return pages


def load_persona(analyst_slug: str) -> str:
    persona_file = PERSONAS_DIR / f"{analyst_slug}.md"
    if persona_file.exists():
        return persona_file.read_text(encoding="utf-8")
    return f"You are {analyst_slug.replace('_', ' ').title()}, a financial analyst."


def build_system_prompt(analyst_slug: str, wiki_pages: dict[str, str]) -> str:
    persona = load_persona(analyst_slug)

    if not wiki_pages:
        wiki_section = "*(No wiki pages available yet — wiki has not been built for this analyst.)*"
    else:
        wiki_section = "\n\n---\n\n".join(
            f"## {name.replace('-', ' ').title()}\n\n{content}"
            for name, content in wiki_pages.items()
        )

    return f"""{persona}

---

# Your Research Notes

{wiki_section}
"""


def check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True
    pwd = st.secrets.get("APP_PASSWORD")
    if not pwd:
        return True
    entered = st.text_input("Password", type="password", key="pw_input")
    if st.button("Enter"):
        if entered == pwd:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    return False


def main():
    st.set_page_config(page_title="Analyst Brains", page_icon="🧠", layout="wide")

    if not check_password():
        st.stop()

    with st.sidebar:
        st.title("🧠 Analyst Brains")
        analyst_name = st.selectbox("Select analyst", list(ANALYSTS.keys()))
        analyst_slug = ANALYSTS[analyst_name]

        wiki_pages = load_wiki(analyst_slug)
        if wiki_pages:
            st.success(f"{len(wiki_pages)} wiki page(s) loaded")
            with st.expander("Wiki pages"):
                for name in wiki_pages:
                    st.markdown(f"- {name.replace('-', ' ').title()}")
        else:
            st.warning("No wiki built yet. Run llmwiki to generate it.")

        if st.button("Clear chat"):
            st.session_state.messages = []
            st.rerun()

    st.title(f"Chat with {analyst_name}")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input(f"Ask {analyst_name} anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        system_prompt = build_system_prompt(analyst_slug, wiki_pages)

        api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")
        if not api_key:
            st.error("ANTHROPIC_API_KEY not found. Set it in .env or Streamlit secrets.")
            st.stop()

        client = anthropic.Anthropic(api_key=api_key)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""

            with client.messages.stream(
                model=MODEL,
                max_tokens=2048,
                system=system_prompt,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})


if __name__ == "__main__":
    main()
