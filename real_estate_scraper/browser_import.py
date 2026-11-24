from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from .models import Listing
from .normalize import from_browser_record, plain


def load_browser_export(path: Path, max_age_hours: float = 30, neighborhoods: tuple[str, ...] = ()) -> tuple[list[Listing], list[str]]:
    if not path.exists():
        return [], [f"No existe la exportacion de navegador: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [], [f"Exportacion de navegador invalida: {exc}"]

    warnings: list[str] = []
    collected = payload.get("collected_at")
    if collected:
        try:
            timestamp = datetime.fromisoformat(str(collected).replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)).total_seconds() / 3600
            if age > max_age_hours:
                return [], [f"La exportacion de navegador tiene {age:.1f} horas y fue ignorada"]
        except ValueError:
            warnings.append("La exportacion no tiene una fecha valida; se utilizara igualmente")

    listings: list[Listing] = []
    seen: set[tuple[str, str]] = set()
    skipped_outside_neighborhoods: dict[str, int] = {}
    sources = payload.get("sources") or {}
    for source in ("mercadolibre", "zonaprop", "argenprop"):
        records = sources.get(source) or []
        if not isinstance(records, list):
            warnings.append(f"La fuente {source} no contiene una lista valida")
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            item = from_browser_record(record, source)
            identity = (source, item.item_id or item.url)
            if identity in seen:
                continue
            if neighborhoods:
                normalized = plain(item.neighborhood)
                matched_neighborhood = None
                for name in sorted(neighborhoods, key=len, reverse=True):
                    if plain(name) in normalized:
                        matched_neighborhood = name
                        break
                if matched_neighborhood is None:
                    skipped_outside_neighborhoods[source] = skipped_outside_neighborhoods.get(source, 0) + 1
                    continue
                item.neighborhood = matched_neighborhood
            seen.add(identity)
            listings.append(item)
    for source, count in skipped_outside_neighborhoods.items():
        warnings.append(f"Se ignoraron {count} avisos promocionados de {source} por estar fuera de los barrios buscados")
    return listings, warnings
