from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from .models import Listing


SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
  item_id TEXT NOT NULL, observed_at TEXT NOT NULL, title TEXT, url TEXT,
  price REAL, currency TEXT, neighborhood TEXT, covered_m2 REAL, total_m2 REAL,
  rooms REAL, bedrooms REAL, parking REAL, status TEXT, score REAL,
  PRIMARY KEY (item_id, observed_at)
);
CREATE INDEX IF NOT EXISTS observations_item ON observations(item_id);
CREATE TABLE IF NOT EXISTS property_observations (
  property_key TEXT NOT NULL, observed_at TEXT NOT NULL, source TEXT,
  source_item_id TEXT, sources TEXT, source_urls TEXT, title TEXT, url TEXT,
  price REAL, currency TEXT, neighborhood TEXT, covered_m2 REAL, total_m2 REAL,
  rooms REAL, bedrooms REAL, parking REAL, status TEXT, score REAL,
  PRIMARY KEY (property_key, observed_at)
);
CREATE INDEX IF NOT EXISTS property_observations_key
  ON property_observations(property_key);
"""


def save(path: Path, listings: list[Listing]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA)
        db.executemany(
            "INSERT OR REPLACE INTO property_observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [(x.property_key or x.item_id, now, x.source, x.item_id,
              ", ".join(sorted(x.source_ids or {x.source: x.item_id})),
              json.dumps(x.source_urls or {x.source: x.url}, ensure_ascii=False),
              x.title, x.url, x.price, x.currency, x.neighborhood,
              x.covered_m2, x.total_m2, x.rooms, x.bedrooms, x.parking, x.status,
              x.opportunity_score) for x in listings],
        )


def add_previous_prices(path: Path, listings: list[Listing]) -> None:
    if not path.exists():
        return
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA)
        try:
            rows = db.execute("""
                SELECT o.property_key, o.price FROM property_observations o
                JOIN (
                  SELECT property_key, MAX(observed_at) AS latest
                  FROM property_observations GROUP BY property_key
                ) p ON p.property_key = o.property_key AND p.latest = o.observed_at
            """).fetchall()
        except sqlite3.OperationalError:
            rows = []
        legacy = dict(db.execute("""
            SELECT o.item_id, o.price FROM observations o
            JOIN (
              SELECT item_id, MAX(observed_at) AS latest
              FROM observations GROUP BY item_id
            ) p ON p.item_id = o.item_id AND p.latest = o.observed_at
        """).fetchall())
    prior = dict(rows)
    for item in listings:
        old = prior.get(item.property_key or item.item_id)
        if old is None:
            old = legacy.get(item.item_id)
        if old is None or item.currency != "USD":
            continue
        item.previous_price_usd = float(old)
        item.price_change_usd = item.price - item.previous_price_usd
        if item.previous_price_usd:
            item.price_change_percent = item.price_change_usd / item.previous_price_usd
