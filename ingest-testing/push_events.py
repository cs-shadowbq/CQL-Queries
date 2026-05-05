#!/usr/bin/env python3
"""
Ingest correlate() test events into CrowdStrike NGSIEM via HEC endpoint.

Reads events from a JSON file (default: events.json).
Timestamps are rebased to now at runtime so events always land within
the current retention window and are queryable in the last ~4 hours.

Uses the HEC /services/collector endpoint with JSON-CQLTest parser.
Each event must have a 'timestamp' field (ISO 8601).

No third-party dependencies — uses stdlib only.

Usage:
  export LOGSCALE_HOST=https://<cid-ngsiem-connect_id>.ingest.us-1.crowdstrike.com
  export LOGSCALE_TOKEN=<your-api-key>
  python3 push_events.py [path/to/events.json]

  Or set HOST and TOKEN directly in the Configuration block below.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
# Values here are overridden by environment variables if set.
HOST  = os.environ.get("LOGSCALE_HOST",  "https://<cid-ngsiem-connect_id>.ingest.us-1.crowdstrike.com")
TOKEN = os.environ.get("LOGSCALE_TOKEN", "<your-api-key>")
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_EVENTS_FILE = Path(__file__).parent / "events.json"


def load_events(path: Path) -> list[dict]:
    """Load a flat JSON array of log event objects."""
    with open(path) as f:
        events = json.load(f)
    timestamps = [datetime.fromisoformat(e["timestamp"]).astimezone(timezone.utc) for e in events]
    earliest, latest = min(timestamps), max(timestamps)
    span = int((latest - earliest).total_seconds() // 60)
    print(f"  Loaded {len(events)} events from {path.name}")
    print(f"  File range:  {earliest.strftime('%Y-%m-%dT%H:%M UTC')} – {latest.strftime('%Y-%m-%dT%H:%M UTC')} (span {span} min)")
    return events


def rebase_timestamps(events: list[dict]) -> list[dict]:
    """Shift all event timestamps so the latest event lands at approximately now.

    The relative spacing between events is preserved.  The file's original
    timestamps are used only to derive offsets — absolute dates are ignored.
    """
    timestamps = [
        datetime.fromisoformat(e["timestamp"]).astimezone(timezone.utc)
        for e in events
    ]
    latest = max(timestamps)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    delta = now - latest

    rebased = []
    for e, orig in zip(events, timestamps):
        e = dict(e)
        e["timestamp"] = (orig + delta).strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
        rebased.append(e)

    earliest = min(datetime.fromisoformat(e["timestamp"]) for e in rebased)
    span = int((now - earliest).total_seconds() // 60)
    print(f"  Rebased to:  {earliest.strftime('%Y-%m-%dT%H:%M UTC')} – {now.strftime('%Y-%m-%dT%H:%M UTC')} (span {span} min)")
    return rebased


def to_epoch(ts_str: str) -> int:
    """Convert ISO 8601 timestamp string to epoch seconds for HEC."""
    dt = datetime.fromisoformat(ts_str)
    return int(dt.astimezone(timezone.utc).timestamp())


def ingest(events: list[dict]) -> None:
    """Send events to the CrowdStrike NGSIEM HEC endpoint (/services/collector)."""
    # HEC format: newline-delimited JSON objects, each wrapping one event.
    # NOT a JSON array — each line is {"time": <epoch>, "event": {...}}.
    payload = "\n".join(
        json.dumps({"time": to_epoch(e["timestamp"]), "event": e})
        for e in events
    ).encode()

    req = urllib.request.Request(
        url=f"{HOST}/services/collector",
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            print(f"\nHTTP {resp.status} — {len(events)} events ingested successfully")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\nHTTP {e.code} error: {body}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    events_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_EVENTS_FILE

    if not events_file.exists():
        print(f"Error: events file not found: {events_file}", file=sys.stderr)
        sys.exit(1)

    if "<cid-ngsiem-connect_id>" in HOST:
        print("Error: set LOGSCALE_HOST with your connect ID (env var or script constant)", file=sys.stderr)
        sys.exit(1)

    if "<your-" in HOST or "<your-" in TOKEN:
        print("Error: set LOGSCALE_HOST and LOGSCALE_TOKEN (env vars or script constants)", file=sys.stderr)
        sys.exit(1)

    print(f"Events file : {events_file}")
    print(f"Target host : {HOST}\n")

    events = load_events(events_file)
    events = rebase_timestamps(events)
    ingest(events)
    print("Done. Wait ~5s, then run your correlate() queries over the last 4h.")


if __name__ == "__main__":
    main()
