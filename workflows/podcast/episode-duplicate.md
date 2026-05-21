# Workflow: Duplicate a Megaphone Episode

## Objective

Copy a single episode (metadata + audio URL) from one Megaphone podcast to another podcast in the same account and network. The audio file is not re-uploaded — both podcasts share the same audio URL.

---

## When to Use

- Cross-posting an episode to a companion or network feed
- Repurposing content from one show to another
- Publishing the same episode under a different podcast brand

---

## Inputs

| Input | Description |
|-------|-------------|
| Source podcast ID | Megaphone podcast ID for the show with the original episode |
| Episode ID | Megaphone episode ID to duplicate |
| Destination podcast ID | Megaphone podcast ID for the target show |

---

## Tools

| Tool | When to use |
|------|------------|
| `tools/megaphone/app.py` | GUI — recommended for interactive use |
| `tools/megaphone/duplicate_episode.py` | CLI — for scripting or agent-orchestrated runs |

**First-time setup (creates a local virtual environment):**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r tools/megaphone/requirements.txt
```

---

## GUI (Streamlit)

```bash
source .venv/bin/activate
streamlit run tools/megaphone/app.py
```

Opens at `http://localhost:8501`. The UI will:
1. Load all podcasts from the account into dropdowns
2. Auto-populate episodes when a source podcast is selected
3. Show a metadata preview for the selected episode
4. Let you pick a destination podcast and click **Duplicate episode**
5. Display the new episode ID and a direct link to Megaphone on success

---

## CLI Steps

### 1. Find podcast IDs (if unknown)

```bash
python tools/megaphone/duplicate_episode.py --list-podcasts
```

Outputs a table of all podcasts in the account with their IDs.

### 2. Find the episode ID (if unknown)

```bash
python tools/megaphone/duplicate_episode.py \
  --source-podcast SOURCE_PODCAST_ID \
  --list-episodes
```

Outputs episode IDs, pub dates, and titles for the source podcast.

### 3. Preview the copy (recommended)

```bash
python tools/megaphone/duplicate_episode.py \
  --source-podcast SOURCE_PODCAST_ID \
  --episode-id EPISODE_ID \
  --dest-podcast DEST_PODCAST_ID \
  --dry-run
```

Prints the exact payload that would be sent to Megaphone without creating anything.

### 4. Duplicate the episode

```bash
python tools/megaphone/duplicate_episode.py \
  --source-podcast SOURCE_PODCAST_ID \
  --episode-id EPISODE_ID \
  --dest-podcast DEST_PODCAST_ID
```

On success, prints the new episode ID and a direct Megaphone CMS link.

---

## What Gets Copied

| Field | Copied |
|-------|--------|
| Title | Yes |
| Pub date | Yes (original date preserved) |
| Author | Yes |
| Summary / description | Yes |
| Subtitle | Yes |
| Show notes (body) | Yes |
| Explicit flag | Yes |
| Episode type (full/trailer/bonus) | Yes |
| Keywords | Yes |
| Season / episode number | Yes |
| Draft status | Yes (preserves source draft/published state) |
| Audio file URL | Yes (shared URL — no re-upload) |
| Episode artwork | Yes (backgroundImageFileId) |

---

## What Does NOT Get Copied

- Podcast-level artwork (set on the destination podcast itself)
- Ad insertion markers (Megaphone Dynamo settings)
- Sponsorship/monetization settings

---

## Edge Cases

- **Episode already exists in destination** — Megaphone will create a duplicate; check for duplicates with `--list-episodes` before running.
- **Podcast not found** — Confirm the podcast ID with `--list-podcasts`. IDs are case-sensitive.
- **Audio URL is private/expired** — If the source audio URL requires authentication or has expired, listeners on the destination feed will get a broken file. Verify the source audio URL is publicly accessible.
- **401 Unauthorized** — `MEGAPHONE_API_KEY` is missing or incorrect in `.env`.

---

## Environment Variables Required

```
MEGAPHONE_API_KEY=
```
