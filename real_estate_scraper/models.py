from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Listing:
    item_id: str
    title: str
    url: str
    price: float
    currency: str
    neighborhood: str
    source: str = "mercadolibre"
    property_key: str = ""
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    rooms: float | None = None
    bedrooms: float | None = None
    bathrooms: float | None = None
    covered_m2: float | None = None
    total_m2: float | None = None
    parking: float | None = None
    description: str = ""
    thumbnail: str = ""
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    price_usd: float | None = None
    usd_per_m2: float | None = None
    corridor_score: float = 0
    opportunity_score: float = 0
    neighborhood_median: float | None = None
    previous_price_usd: float | None = None
    price_change_usd: float | None = None
    price_change_percent: float | None = None
    status: str = "rejected"
    reasons: list[str] = field(default_factory=list)
    source_ids: dict[str, str] = field(default_factory=dict)
    source_urls: dict[str, str] = field(default_factory=dict)
    source_prices: dict[str, float] = field(default_factory=dict)
    duplicate_count: int = 1
    dedupe_confidence: str = "single"
