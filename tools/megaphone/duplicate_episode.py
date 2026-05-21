#!/usr/bin/env python3
"""
duplicate_episode.py — Copy a single Megaphone episode from one podcast to another.

Usage:
  python duplicate_episode.py --list-podcasts
  python duplicate_episode.py --list-episodes --source-podcast PODCAST_ID
  python duplicate_episode.py --source-podcast PODCAST_ID --episode-id EPISODE_ID --dest-podcast PODCAST_ID
  python duplicate_episode.py --source-podcast PODCAST_ID --episode-id EPISODE_ID --dest-podcast PODCAST_ID --dry-run

Requires MEGAPHONE_API_KEY in .env (or environment).
"""

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MEGAPHONE_API_KEY")
BASE_URL = "https://cms.megaphone.fm/api"

# Fields to copy from source episode to destination.
# audioFileUrl is included so both podcasts share the same audio asset.
COPYABLE_FIELDS = [
    "title",
    "pubDate",
    "author",
    "summary",
    "subtitle",
    "explicit",
    "episodeType",
    "keywords",
    "season",
    "episodeNumber",
    "draft",
    "audioFileUrl",
    "backgroundImageFileId",
]


def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def list_podcasts():
    r = requests.get(f"{BASE_URL}/podcasts", headers=_headers())
    r.raise_for_status()
    return r.json()


def list_episodes(podcast_id, page=1, per=50):
    r = requests.get(
        f"{BASE_URL}/podcasts/{podcast_id}/episodes",
        headers=_headers(),
        params={"page": page, "per": per},
    )
    r.raise_for_status()
    return r.json()


def get_episode(podcast_id, episode_id):
    r = requests.get(
        f"{BASE_URL}/podcasts/{podcast_id}/episodes/{episode_id}",
        headers=_headers(),
    )
    r.raise_for_status()
    return r.json()


def create_episode(podcast_id, payload):
    r = requests.post(
        f"{BASE_URL}/podcasts/{podcast_id}/episodes",
        headers=_headers(),
        json=payload,
    )
    r.raise_for_status()
    return r.json()


def build_payload(source):
    payload = {}
    for key in COPYABLE_FIELDS:
        if source.get(key) is not None:
            payload[key] = source[key]

    # Show notes may live under different keys depending on API version
    for body_key in ("body", "episodeBody", "contentBody"):
        if source.get(body_key):
            payload[body_key] = source[body_key]
            break

    return payload


def cmd_list_podcasts():
    podcasts = list_podcasts()
    if not podcasts:
        print("No podcasts found.")
        return
    print(f"\n{'ID':<36} Title")
    print("-" * 70)
    for p in podcasts:
        print(f"{p['id']:<36} {p['title']}")


def cmd_list_episodes(podcast_id):
    episodes = list_episodes(podcast_id)
    if not episodes:
        print(f"No episodes found in podcast {podcast_id}.")
        return
    print(f"\n{'ID':<36} {'Pub Date':<26} Title")
    print("-" * 90)
    for ep in episodes:
        print(f"{ep['id']:<36} {str(ep.get('pubDate', '')):<26} {ep.get('title', '')}")


def cmd_duplicate(source_podcast, episode_id, dest_podcast, dry_run):
    print(f"Fetching episode {episode_id} from podcast {source_podcast}...")
    source = get_episode(source_podcast, episode_id)

    print(f"  Title:    {source.get('title')}")
    print(f"  Pub date: {source.get('pubDate')}")
    print(f"  Audio:    {source.get('audioFileUrl', '(none)')}")
    print(f"  Draft:    {source.get('draft', False)}")

    payload = build_payload(source)

    if dry_run:
        print("\n-- DRY RUN: payload that would be POSTed to destination --")
        print(json.dumps(payload, indent=2))
        return

    print(f"\nCreating episode in destination podcast {dest_podcast}...")
    result = create_episode(dest_podcast, payload)

    print("\nDone.")
    print(f"  New episode ID: {result.get('id')}")
    print(f"  Title:          {result.get('title')}")
    print(f"  Status:         {'Draft' if result.get('draft') else 'Published'}")
    ep_id = result.get("id", "")
    print(f"  Megaphone URL:  https://cms.megaphone.fm/channel/{dest_podcast}/episodes/{ep_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Duplicate a Megaphone episode to another podcast in the same account.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--list-podcasts", action="store_true", help="List all podcasts in the account")
    parser.add_argument("--list-episodes", action="store_true", help="List episodes in --source-podcast")
    parser.add_argument("--source-podcast", metavar="ID", help="Source podcast ID")
    parser.add_argument("--episode-id", metavar="ID", help="Episode ID to duplicate")
    parser.add_argument("--dest-podcast", metavar="ID", help="Destination podcast ID")
    parser.add_argument("--dry-run", action="store_true", help="Show payload without creating the episode")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: MEGAPHONE_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    if args.list_podcasts:
        cmd_list_podcasts()
        return

    if args.list_episodes:
        if not args.source_podcast:
            parser.error("--list-episodes requires --source-podcast")
        cmd_list_episodes(args.source_podcast)
        return

    if not all([args.source_podcast, args.episode_id, args.dest_podcast]):
        parser.print_help()
        sys.exit(1)

    cmd_duplicate(args.source_podcast, args.episode_id, args.dest_podcast, args.dry_run)


if __name__ == "__main__":
    main()
