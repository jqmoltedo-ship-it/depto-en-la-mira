#!/usr/bin/env python3
"""Convierte snapshot.csv en un payload JSON tipado para Google Sheets."""

from __future__ import annotations

from collections import Counter
import csv
from datetime import datetime
import json
from pathlib import Path
from statistics import median
import sys


NUMERIC = {
    "puntaje", "precio_usd", "precio_anterior_usd", "cambio_precio_usd",
    "cambio_precio_pct", "usd_m2_cubierto", "ambientes", "dormitorios",
    "cubiertos_m2", "total_m2", "cocheras", "duplicados",
}


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/snapshot.csv")
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        headers = list(reader.fieldnames or [])
        raw_rows = list(reader)

    rows = []
    for raw in raw_rows:
        row = []
        for header in headers:
            value = raw.get(header, "")
            if value == "":
                row.append(None)
            elif header in NUMERIC:
                row.append(float(value))
            else:
                row.append(value)
        rows.append(row)

    prices = [float(row["precio_usd"]) for row in raw_rows if row["precio_usd"]]
    covered = [float(row["cubiertos_m2"]) for row in raw_rows if row["cubiertos_m2"]]
    status = Counter(row["estado"] for row in raw_rows)
    source_counts = Counter()
    for row in raw_rows:
        for source in filter(None, (part.strip() for part in row["fuentes"].split(","))):
            source_counts[source] += 1
    observed = datetime.fromisoformat(raw_rows[0]["observado_el"]) if raw_rows else datetime.now().astimezone()
    summary = {
        "date": observed.date().isoformat(),
        "analyzed": len(raw_rows),
        "matches": status["match"],
        "review": status["review"],
        "rejected": status["rejected"],
        "new": sum(not row["precio_anterior_usd"] for row in raw_rows),
        "decreases": sum(bool(row["cambio_precio_usd"]) and float(row["cambio_precio_usd"]) < 0 for row in raw_rows),
        "increases": sum(bool(row["cambio_precio_usd"]) and float(row["cambio_precio_usd"]) > 0 for row in raw_rows),
        "median_price": median(prices) if prices else 0,
        "max_covered": max(covered) if covered else 0,
        "duplicates_grouped": sum(max(0, int(float(row["duplicados"] or 1)) - 1) for row in raw_rows),
        "source_counts": dict(source_counts),
    }
    json.dump({"headers": headers, "rows": rows, "summary": summary}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
