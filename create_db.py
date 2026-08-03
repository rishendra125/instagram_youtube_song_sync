#!/usr/bin/env python3
"""
Local song database for the Instagram -> YouTube playlist pipeline.

Stage 1: pure local storage. No API calls, no network. Run this on your desktop
to create (or update) songs.db next to this script.

Re-running is SAFE: the UNIQUE(title, artist) constraint + INSERT OR IGNORE means
duplicates are never created, so you can feed it "new additions only" each time
without worrying about re-adding a song already stored.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("songs.db")


def mmss_to_seconds(mmss: str) -> int:
    """'4:38' -> 278.  Used later for duration-matching against YouTube results."""
    m, s = mmss.split(":")
    return int(m) * 60 + int(s)


# ---------------------------------------------------------------------------
# Songs read from the Instagram "Saved music" screenshot (IMG_2061.png).
# 'reels' counts are dropped on purpose - they're IG engagement metadata,
# not song data. Duration is kept because it's our YouTube-match tiebreaker.
# ---------------------------------------------------------------------------
SONGS = [
    # title,                     artist,                 duration
    ("Frozen in Time",           "Al Di Meola",          "3:25"),
    ("Usedtothis",               "David Ryan Harris",    "3:56"),
    ("Entre Nous",               "Rush",                 "4:38"),
    ("These Chains",             "Toto",                 "4:58"),
    ("It Leads to This",         "The Pineapple Thief",  "4:44"),
    ("Birds",                    "Katatonia",            "4:09"),
    ("...but it won't kill me",  "DISTANCE : DIVINE",    "4:20"),
    ("Stratus",                  "I Built the Sky",      "3:46"),
    ("Haru",                     "Satoshi Gogo",         "3:05"),
    ("Knot",                     "Chon",                 "3:03"),
    ("of bliss",                 "David Maxim Micic",    "1:54"),  # bottom row, partly cut off - verify
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS songs (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    title                 TEXT NOT NULL,
    artist                TEXT NOT NULL,
    duration              TEXT,              -- as seen on screenshot, e.g. '4:38'
    duration_seconds      INTEGER,           -- normalized, for YouTube duration matching
    source                TEXT DEFAULT 'instagram',
    date_captured         TEXT DEFAULT (datetime('now')),

    -- filled in later, during the YouTube stage:
    youtube_video_id      TEXT,
    youtube_url           TEXT,
    match_status          TEXT DEFAULT 'pending',
        -- pending -> needs_review / auto_confirmed -> added / skipped
    date_added_to_playlist TEXT,
    notes                 TEXT,

    UNIQUE(title, artist)
);
"""


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    inserted = 0
    for title, artist, dur in SONGS:
        cur.execute(
            """INSERT OR IGNORE INTO songs (title, artist, duration, duration_seconds)
               VALUES (?, ?, ?, ?)""",
            (title, artist, dur, mmss_to_seconds(dur)),
        )
        inserted += cur.rowcount  # 1 if newly inserted, 0 if it already existed

    conn.commit()

    total = cur.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
    print(f"DB: {DB_PATH}")
    print(f"Newly added this run: {inserted}")
    print(f"Total songs in database: {total}\n")

    print(f"{'id':>2}  {'title':28}  {'artist':22}  {'dur':>5}  status")
    print("-" * 78)
    for row in cur.execute(
        "SELECT id, title, artist, duration, match_status FROM songs ORDER BY id"
    ):
        rid, title, artist, dur, status = row
        print(f"{rid:>2}  {title:28.28}  {artist:22.22}  {dur:>5}  {status}")

    conn.close()


if __name__ == "__main__":
    main()
