from __future__ import annotations

from collections import defaultdict
from statistics import median

from .config import Requirements
from .models import Listing
from .normalize import plain


def evaluate(listing: Listing, req: Requirements, corridor_terms: list[str], renovation_terms: list[str]) -> Listing:
    listing.reasons = []
    neighborhood = plain(listing.neighborhood)
    allowed = {plain(name) for name in req.neighborhoods}
    if neighborhood not in allowed:
        listing.reasons.append("barrio fuera de la busqueda")
    if listing.currency != "USD" or not (req.min_price_usd <= listing.price <= req.max_price_usd):
        listing.reasons.append("precio fuera de rango o no publicado en USD")
    required = [
        ("ambientes", listing.rooms, req.min_rooms),
        ("m2 totales", listing.total_m2, req.min_total_m2),
        ("cocheras", listing.parking, req.min_parking),
    ]
    missing = [name for name, value, _ in required if value is None]
    insufficient = [name for name, value, minimum in required if value is not None and value < minimum]
    listing.reasons.extend(f"falta {name}" for name in missing)
    listing.reasons.extend(f"{name} insuficiente" for name in insufficient)
    listing.status = "review" if missing and not any("fuera" in r or "insuficiente" in r for r in listing.reasons) else "rejected"
    if not listing.reasons:
        listing.status = "match"
        listing.price_usd = listing.price
        listing.usd_per_m2 = listing.price / listing.total_m2
    haystack = plain(" ".join([listing.title, listing.address, listing.description, listing.neighborhood]))
    hits = sum(1 for term in corridor_terms if plain(term) in haystack)
    listing.corridor_score = min(1.0, hits / 2)
    if any(plain(term) in haystack for term in renovation_terms):
        listing.corridor_score = min(1.0, listing.corridor_score + 0.1)
    return listing


def rank(listings: list[Listing]) -> list[Listing]:
    groups: dict[str, list[float]] = defaultdict(list)
    for item in listings:
        if item.status == "match" and item.usd_per_m2:
            groups[plain(item.neighborhood)].append(item.usd_per_m2)
    medians = {key: median(values) for key, values in groups.items()}
    for item in listings:
        if item.status != "match" or not item.usd_per_m2:
            continue
        item.neighborhood_median = medians[plain(item.neighborhood)]
        discount = max(-0.5, min(0.5, 1 - item.usd_per_m2 / item.neighborhood_median))
        item.opportunity_score = round(50 + discount * 80 + item.corridor_score * 10, 1)
    return sorted(listings, key=lambda x: (x.status == "match", x.opportunity_score), reverse=True)
