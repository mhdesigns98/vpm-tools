#!/usr/bin/env python3
"""
debug_api.py — Print raw Megaphone API responses to diagnose episode fetching.

Run with:
  python tools/megaphone/debug_api.py
"""

import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MEGAPHONE_API_KEY")
NETWORK_ID = os.getenv("MEGAPHONE_NETWORK_ID", "")
BASE_URL = "https://cms.megaphone.fm/api"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ── 1. Podcasts ────────────────────────────────────────────────
section("PODCASTS RESPONSE")

podcasts_url = f"{BASE_URL}/networks/{NETWORK_ID}/podcasts" if NETWORK_ID else f"{BASE_URL}/podcasts"
print(f"URL: {podcasts_url}\n")

r = requests.get(podcasts_url, headers=headers)
print(f"Status: {r.status_code}")
print(f"Response headers:")
for k, v in r.headers.items():
    print(f"  {k}: {v}")

podcasts = r.json()
print(f"\nPodcast count: {len(podcasts)}")
for p in podcasts:
    print(f"  [{p.get('id')}] {p.get('title')}")

# ── 2. Pick VPM Daily Newscast ─────────────────────────────────
target = next((p for p in podcasts if "daily newscast" in (p.get("title") or "").lower()), None)
if not target:
    print("\nCould not find VPM Daily Newscast — using first podcast instead")
    target = podcasts[0] if podcasts else None

if not target:
    print("No podcasts found. Exiting.")
    sys.exit(1)

podcast_id = target["id"]
print(f"\nUsing podcast: {target.get('title')} ({podcast_id})")

# ── 3. Episodes page 1 ─────────────────────────────────────────
section("EPISODES — PAGE 1 (raw)")

ep_url = f"{BASE_URL}/networks/{NETWORK_ID}/podcasts/{podcast_id}/episodes" if NETWORK_ID else f"{BASE_URL}/podcasts/{podcast_id}/episodes"
print(f"URL: {ep_url}\n")

r2 = requests.get(ep_url, headers=headers, params={"page": 1, "per": 50})
print(f"Status: {r2.status_code}")
print(f"Response headers:")
for k, v in r2.headers.items():
    print(f"  {k}: {v}")

episodes = r2.json()
print(f"\nEpisodes returned: {len(episodes)}")
print(f"\nFirst 5 episodes:")
for ep in episodes[:5]:
    print(f"  title={ep.get('title')!r}")
    print(f"  id={ep.get('id')}")
    print(f"  pubDate={ep.get('pubDate')}")
    print(f"  keys={list(ep.keys())}")
    print()

# ── 4. Episodes page 2 ─────────────────────────────────────────
section("EPISODES — PAGE 2")

r3 = requests.get(ep_url, headers=headers, params={"page": 2, "per": 50})
print(f"Status: {r3.status_code}")
episodes_p2 = r3.json()
print(f"Episodes returned: {len(episodes_p2)}")
if episodes_p2:
    print(f"First episode on page 2: {episodes_p2[0].get('title')!r}")
    same_as_p1 = episodes_p2[0].get("id") == episodes[0].get("id")
    print(f"Same as page 1 first episode? {same_as_p1}")

# ── 5. Full episode object ─────────────────────────────────────
if episodes:
    section("FULL EPISODE OBJECT (first episode)")
    print(json.dumps(episodes[0], indent=2))
