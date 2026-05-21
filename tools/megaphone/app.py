"""
Megaphone Episode Duplicator — Streamlit GUI

Run with:
  streamlit run tools/megaphone/app.py
"""

import os
import re

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MEGAPHONE_API_KEY")
BASE_URL = "https://cms.megaphone.fm/api"

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
):
    r = requests.get(
        f"{BASE_URL}/networks/{source_network_id}/podcasts/{source_podcast_id}/episodes/{episode_id}",
        headers=_headers(),
    )
    r.raise_for_status()
    source = r.json()

    payload = {
        "title": move_date_to_end(source.get("title") or ""),
        "pubdate": source.get("pubdate"),
        "author": source.get("author"),
        "summary": source.get("summary"),
        "subtitle": source.get("subtitle"),
        "explicit": source.get("explicit"),
        "episodeType": source.get("episodeType"),
        "episodeNumber": source.get("episodeNumber"),
        "seasonNumber": source.get("seasonNumber"),
        "draft": source.get("draft"),
        "originalUrl": source.get("downloadUrl"),  # permanent CDN URL
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    r2 = requests.post(
        f"{BASE_URL}/networks/{dest_network_id}/podcasts/{dest_podcast_id}/episodes",
        headers=_headers(),
        json=payload,
    )
    r2.raise_for_status()
    return source, r2.json()


# ── UI ────────────────────────────────────────────────────────────────────────

st.title("🎙️ Megaphone Episode Duplicator")
st.caption("Copy an episode from one podcast to another within the same account.")

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

# Episode metadata preview
if episode_id:
    ep = ep_map[episode_id]
    with st.expander("Episode details", expanded=True):
        col1, col2 = st.columns(2)
        original_title = ep.get("title", "—")
        reformatted = move_date_to_end(original_title)
        if reformatted != original_title:
            col1.markdown(f"**Title (original)**  \n{original_title}")
            col1.markdown(f"**Title on duplicate** ✎  \n{reformatted}")
        else:
            col1.markdown(f"**Title**  \n{original_title}")
        col1.markdown(f"**Pub date**  \n{str(ep.get('pubdate', '—'))[:10]}")
        col1.markdown(f"**Type**  \n{ep.get('episodeType', '—').capitalize()}")
        col2.markdown(f"**Author**  \n{ep.get('author', '—')}")
        col2.markdown(f"**Explicit**  \n{'Yes' if ep.get('explicit') else 'No'}")
        col2.markdown(f"**Draft**  \n{'Yes' if ep.get('draft') else 'No'}")
        if ep.get("audioFileUrl"):
            st.markdown(f"**Audio URL**  \n`{ep['audioFileUrl']}`")
        if ep.get("summary"):
            st.markdown(f"**Summary**  \n{ep['summary']}")

st.divider()

# ── Destination podcast ────────────────────────────────────────────────────────
st.subheader("2. Destination")

if multi_network:
    use_test = st.toggle("Use test network", value=True, key="use_test_network")
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

st.divider()

# ── Duplicate button ───────────────────────────────────────────────────────────
st.subheader("3. Duplicate")

col_btn, col_status = st.columns([1, 3])

with col_btn:
    go = st.button("Duplicate episode", type="primary", use_container_width=True)

if go:
    src_title = podcast_map[source_id]
    dst_title = podcast_map[dest_id]
    ep_title = ep_map[episode_id].get("title", episode_id)

    with st.spinner(f'Duplicating "{ep_title}" into {dst_title}...'):
        try:
            source_ep, new_ep = duplicate_episode(
                source_id, episode_id, source_network_id, dest_id, dest_network_id
            )
            new_id = new_ep.get("id", "")
            megaphone_url = f"https://cms.megaphone.fm/channel/{dest_id}/episodes/{new_id}"

            st.success("Episode duplicated successfully!")
            st.markdown(
                f"**New episode ID:** `{new_id}`  \n"
                f"**In podcast:** {dst_title}  \n"
                f"**Status:** {'Draft' if new_ep.get('draft') else 'Published'}  \n"
                f"**[Open in Megaphone →]({megaphone_url})**"
            )
            # Bust episode cache so destination reflects the new episode
            fetch_all_episodes.clear()
            fetch_recent_episodes.clear()

        except requests.HTTPError as e:
            st.error(f"Duplication failed: {e.response.status_code} — {e.response.text}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
