"""
Megaphone Episode Duplicator — Streamlit GUI

Run with:
  streamlit run tools/megaphone/app.py
"""

import csv
import os
import re
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# On Streamlit Cloud, secrets live in st.secrets — copy them into os.environ
# so the rest of the app can use os.getenv() uniformly in both environments.
try:
    for _k, _v in st.secrets.items():
        if _k not in os.environ:
            os.environ[_k] = str(_v)
except Exception:
    pass

API_KEY = os.getenv("MEGAPHONE_API_KEY")
BASE_URL = "https://cms.megaphone.fm/api"
MEGAPHONE_ORG_ID = "ea536376-5e75-11ea-92db-07ce7dea6f98"
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "duplication_log.csv")
LOG_FIELDS = ["timestamp", "source_podcast", "source_episode_id", "source_title",
              "dest_podcast", "new_episode_id", "new_title", "status"]

# Support one or more network IDs as a comma-separated list.
# Falls back to the singular MEGAPHONE_NETWORK_ID for backwards compatibility.
_raw_ids = os.getenv("MEGAPHONE_NETWORK_IDS") or os.getenv("MEGAPHONE_NETWORK_ID", "")
NETWORK_IDS = [nid.strip() for nid in _raw_ids.split(",") if nid.strip()]

st.set_page_config(
    page_title="Megaphone Episode Duplicator",
    page_icon="🎙️",
    layout="centered",
)

# ── API helpers ────────────────────────────────────────────────────────────────

def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@st.cache_data(show_spinner=False)
def fetch_podcasts():
    seen, podcasts = set(), []
    for nid in NETWORK_IDS:
        r = requests.get(f"{BASE_URL}/networks/{nid}/podcasts", headers=_headers())
        r.raise_for_status()
        for p in r.json():
            if p.get("id") not in seen:
                seen.add(p["id"])
                p["_networkId"] = nid
                p["_orgId"] = p.get("organizationId", "")
                podcasts.append(p)
    return podcasts


@st.cache_data(show_spinner=False)
def fetch_recent_episodes(podcast_id: str, network_id: str):
    """Fetch page 1 only (100 episodes) sorted newest-first by pubdate."""
    url = f"{BASE_URL}/networks/{network_id}/podcasts/{podcast_id}/episodes"
    r = requests.get(url, headers=_headers(), params={"page": 1, "per": 100})
    r.raise_for_status()
    return sorted(r.json(), key=lambda e: e.get("pubdate") or "", reverse=True)


@st.cache_data(show_spinner=False)
def fetch_all_episodes(podcast_id: str, network_id: str):
    """Fetch every page and return all episodes sorted newest-first by pubdate."""
    url = f"{BASE_URL}/networks/{network_id}/podcasts/{podcast_id}/episodes"
    seen, episodes = set(), []
    page = 1
    while page <= 100:  # safety cap
        r = requests.get(url, headers=_headers(), params={"page": page, "per": 100})
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        new = [ep for ep in batch if ep.get("id") not in seen]
        if not new:
            break
        for ep in new:
            seen.add(ep["id"])
            episodes.append(ep)
        page += 1
    return sorted(episodes, key=lambda e: e.get("pubdate") or "", reverse=True)


# Matches dates at the start of a title, e.g. "05/20/2025", "2025-05-20", "May 20, 2025"
_DATE_PREFIX = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2},? \d{4})"
    r"\s*[-–—:,]?\s*",
    re.IGNORECASE,
)


def move_date_to_end(title: str) -> str:
    m = _DATE_PREFIX.match(title)
    if not m:
        return title
    date_part = m.group(1).strip()
    rest = title[m.end():].strip()
    return f"{rest} - {date_part}" if rest else title


def duplicate_episode(
    source_podcast_id: str,
    episode_id: str,
    source_network_id: str,
    dest_podcast_id: str,
    dest_network_id: str,
    title: str = None,
    as_draft: bool = None,
):
    r = requests.get(
        f"{BASE_URL}/networks/{source_network_id}/podcasts/{source_podcast_id}/episodes/{episode_id}",
        headers=_headers(),
    )
    r.raise_for_status()
    source = r.json()

    # Resolve the download URL to its direct CDN URL (bypass the tracking redirect)
    # so Megaphone's ingestion can fetch it without hitting their own analytics proxy.
    download_url = source.get("downloadUrl")
    if download_url:
        try:
            resolved = requests.head(download_url, allow_redirects=True, timeout=15)
            direct_url = resolved.url
        except Exception:
            direct_url = download_url
    else:
        direct_url = None

    payload = {
        "title": title if title is not None else move_date_to_end(source.get("title") or ""),
        "pubdate": source.get("pubdate"),
        "author": source.get("author"),
        "summary": source.get("summary"),
        "subtitle": source.get("subtitle"),
        "explicit": source.get("explicit"),
        "episodeType": source.get("episodeType"),
        "episodeNumber": source.get("episodeNumber"),
        "seasonNumber": source.get("seasonNumber"),
        "draft": as_draft if as_draft is not None else source.get("draft"),
        "originalUrl": direct_url,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    r2 = requests.post(
        f"{BASE_URL}/networks/{dest_network_id}/podcasts/{dest_podcast_id}/episodes",
        headers=_headers(),
        json=payload,
    )
    r2.raise_for_status()
    return source, r2.json()


def append_log(source_podcast, source_ep_id, source_title, dest_podcast, new_ep_id, new_title, status):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source_podcast": source_podcast,
            "source_episode_id": source_ep_id,
            "source_title": source_title,
            "dest_podcast": dest_podcast,
            "new_episode_id": new_ep_id,
            "new_title": new_title,
            "status": status,
        })


# ── UI ────────────────────────────────────────────────────────────────────────

st.title("🎙️ Megaphone Episode Duplicator")
st.caption("Copy an episode from one podcast to another within the same account.")

APP_PASSWORD = os.getenv("APP_PASSWORD", "")
if APP_PASSWORD:
    pwd = st.text_input("Password", type="password", key="app_password")
    if pwd != APP_PASSWORD:
        if pwd:
            st.error("Incorrect password.")
        st.stop()

if not API_KEY:
    st.error("**MEGAPHONE_API_KEY** is not set. Add it to your `.env` file and restart.")
    st.stop()

if not NETWORK_IDS:
    st.error("**MEGAPHONE_NETWORK_ID** is not set. Add it to your `.env` file and restart.")
    st.stop()

# Load all networks + podcasts
with st.spinner("Loading podcasts…"):
    try:
        podcasts = fetch_podcasts()
    except requests.HTTPError as e:
        st.error(f"Failed to load podcasts: {e}")
        st.stop()

if not podcasts:
    st.warning("No podcasts found in this account.")
    st.stop()

podcast_map = {p["id"]: p["title"] for p in podcasts}
podcast_network_map = {p["id"]: p["_networkId"] for p in podcasts}
podcast_org_map = {p["id"]: p["_orgId"] for p in podcasts}
podcast_ids = list(podcast_map.keys())

multi_network = len(NETWORK_IDS) > 1

# When two networks are configured, pin source to the first and dest to the second.
# With one network, both dropdowns show all podcasts.
source_pool = (
    [p["id"] for p in podcasts if p["_networkId"] == NETWORK_IDS[0]]
    if multi_network else podcast_ids
)
dest_pool = (
    [p["id"] for p in podcasts if p["_networkId"] == NETWORK_IDS[-1]]
    if multi_network else podcast_ids
)

def _podcast_label(pid):
    return podcast_map[pid]


def _podcast_index(name_or_id: str, options: list) -> int:
    for i, pid in enumerate(options):
        if pid == name_or_id:
            return i
        if podcast_map.get(pid, "").lower() == name_or_id.lower():
            return i
    return 0

# Destination Newscast — NPR Feed podcast ID
NEWSCAST_NPR_ID = "6db3810a-44bc-11f1-bd9a-3fdd256297a1"


# ── Source podcast ─────────────────────────────────────────────────────────────
st.subheader("1. Source")

source_id = st.selectbox(
    "Source podcast",
    options=source_pool,
    index=_podcast_index("VPM Daily Newscast", source_pool),
    format_func=_podcast_label,
    key="source_podcast",
)

source_network_id = podcast_network_map[source_id]

show_all = st.toggle("Show all episodes", value=False, key="show_all_episodes")

with st.spinner("Loading all episodes…" if show_all else "Loading recent episodes…"):
    try:
        episodes = (
            fetch_all_episodes(source_id, source_network_id)
            if show_all
            else fetch_recent_episodes(source_id, source_network_id)
        )
    except requests.HTTPError as e:
        st.error(f"Failed to load episodes: {e}")
        st.stop()

if not episodes:
    st.warning("No episodes found in this podcast.")
    st.stop()

ep_map = {ep["id"]: ep for ep in episodes}
ep_options = [ep["id"] for ep in episodes]


def ep_label(eid):
    ep = ep_map.get(eid, {})
    date = str(ep.get("pubdate") or "")[:10]
    draft = " [draft]" if ep.get("draft") else ""
    title = ep.get("title") or "Untitled"
    return f"{title}{draft}  ({date})" if date else f"{title}{draft}"


episode_id = st.selectbox(
    "Episode to duplicate",
    options=ep_options,
    format_func=ep_label,
    key="episode",
)

# Episode metadata preview + editable title
if episode_id:
    ep = ep_map[episode_id]
    original_title = ep.get("title", "")
    reformatted = move_date_to_end(original_title)

    if not ep.get("downloadUrl"):
        st.error("⚠️ This episode has no audio file — duplicating it will create an empty episode. Wait until the source is fully processed before duplicating.")

    final_title = st.text_input(
        "Title for duplicate",
        value=reformatted,
        key=f"title_{episode_id}",
        help="Auto-reformatted from the original. Edit before duplicating if needed.",
    )

    with st.expander("Episode details"):
        col1, col2 = st.columns(2)
        if reformatted != original_title:
            col1.markdown(f"**Original title**  \n{original_title}")
        col1.markdown(f"**Pub date**  \n{str(ep.get('pubdate', '—'))[:10]}")
        col1.markdown(f"**Type**  \n{ep.get('episodeType', '—').capitalize()}")
        col2.markdown(f"**Author**  \n{ep.get('author', '—')}")
        col2.markdown(f"**Explicit**  \n{'Yes' if ep.get('explicit') else 'No'}")
        col2.markdown(f"**Draft**  \n{'Yes' if ep.get('draft') else 'No'}")
        if ep.get("summary"):
            st.markdown(f"**Summary**  \n{ep['summary']}")

st.divider()

# ── Destination podcast ────────────────────────────────────────────────────────
st.subheader("2. Destination")

if multi_network:
    use_test = st.toggle("Send to test network instead", value=False, key="use_test_network")
    active_dest_pool = (
        [p["id"] for p in podcasts if p["_networkId"] == NETWORK_IDS[-1]]
        if use_test
        else [p["id"] for p in podcasts if p["_networkId"] == NETWORK_IDS[0]]
    )
else:
    active_dest_pool = dest_pool

dest_options = [pid for pid in active_dest_pool if pid != source_id]
if not dest_options:
    st.warning("No other podcasts available to copy into.")
    st.stop()

dest_default = NEWSCAST_NPR_ID if NEWSCAST_NPR_ID in dest_options else dest_options[0]
dest_id = st.selectbox(
    "Destination podcast",
    options=dest_options,
    index=_podcast_index(dest_default, dest_options),
    format_func=_podcast_label,
    key="dest_podcast",
)

dest_network_id = podcast_network_map[dest_id]

# Duplicate detection — check if title already exists in destination
if episode_id:
    with st.spinner("Checking for duplicates…"):
        try:
            dest_eps = fetch_recent_episodes(dest_id, dest_network_id)
            dest_titles = {(e.get("title") or "").lower().strip() for e in dest_eps}
            check_title = st.session_state.get(f"title_{episode_id}", reformatted)
            if check_title.lower().strip() in dest_titles:
                st.warning(
                    f"**Possible duplicate:** An episode named \"{check_title}\" already exists "
                    f"in {podcast_map[dest_id]}. You can still proceed if this is intentional."
                )
        except Exception:
            pass

st.divider()

# ── Duplicate button ───────────────────────────────────────────────────────────
st.subheader("3. Duplicate")

as_draft = st.toggle("Create as draft", value=False, key="as_draft",
                     help="Episode will be saved to Megaphone but not published to the feed.")

col_btn, col_status = st.columns([1, 3])

with col_btn:
    go = st.button("Duplicate episode", type="primary", use_container_width=True)

if go:
    src_title = podcast_map[source_id]
    dst_title = podcast_map[dest_id]
    ep_title = ep_map[episode_id].get("title", episode_id)
    use_title = st.session_state.get(f"title_{episode_id}", reformatted)

    with st.spinner(f'Duplicating "{ep_title}" into {dst_title}...'):
        try:
            source_ep, new_ep = duplicate_episode(
                source_id, episode_id, source_network_id, dest_id, dest_network_id,
                title=use_title,
                as_draft=True if as_draft else None,
            )
            new_id = new_ep.get("id", "")
            status = "Draft" if new_ep.get("draft") else "Published"
            megaphone_url = f"https://cms.megaphone.fm/organizations/{MEGAPHONE_ORG_ID}/podcasts/{dest_id}/episodes/{new_id}"

            st.success("Episode duplicated successfully!")
            st.markdown(
                f"**New episode ID:** `{new_id}`  \n"
                f"**In podcast:** {dst_title}  \n"
                f"**Title:** {use_title}  \n"
                f"**Status:** {status}  \n"
                f"**[Open in Megaphone →]({megaphone_url})**"
            )

            append_log(src_title, episode_id, ep_title, dst_title, new_id, use_title, status)

            # Bust episode cache so destination reflects the new episode
            fetch_all_episodes.clear()
            fetch_recent_episodes.clear()

        except requests.HTTPError as e:
            st.error(f"Duplication failed: {e.response.status_code} — {e.response.text}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

st.divider()

# ── Duplication log ────────────────────────────────────────────────────────────
with st.expander("Duplication history"):
    if os.path.isfile(LOG_FILE):
        log_df = pd.read_csv(LOG_FILE)
        st.dataframe(
            log_df.sort_values("timestamp", ascending=False).reset_index(drop=True),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.caption("No duplications logged yet.")
