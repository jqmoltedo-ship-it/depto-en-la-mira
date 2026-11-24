from __future__ import annotations

import re
import unicodedata
from typing import Any

from .models import Listing


ATTRIBUTE_MAP = {
    "ROOMS": "rooms",
    "BEDROOMS": "bedrooms",
    "COVERED_AREA": "covered_m2",
    "TOTAL_AREA": "total_m2",
    "PARKING_LOTS": "parking",
}


def plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(c for c in normalized if not unicodedata.combining(c)).lower()


def number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:[.,]\d+)?", str(value).replace(".", ""))
    return float(match.group().replace(",", ".")) if match else None


def _attr_values(item: dict) -> dict[str, float | None]:
    result = {field: None for field in ATTRIBUTE_MAP.values()}
    for attr in item.get("attributes", []):
        field = ATTRIBUTE_MAP.get(attr.get("id"))
        if field:
            result[field] = number(attr.get("value_name") or attr.get("value_id"))
    return result


def from_api(item: dict, description: str = "") -> Listing:
    location = item.get("location") or {}
    neighborhood = (location.get("neighborhood") or {}).get("name", "")
    address = location.get("address_line") or ""
    geo = item.get("geolocation") or {}
    attrs = _attr_values(item)
    return Listing(
        item_id=str(item.get("id", "")), title=item.get("title") or "",
        url=item.get("permalink") or "", price=float(item.get("price") or 0),
        currency=item.get("currency_id") or "", neighborhood=neighborhood,
        source="mercadolibre",
        address=address, latitude=number(geo.get("latitude") or location.get("latitude")),
        longitude=number(geo.get("longitude") or location.get("longitude")),
        description=description, thumbnail=item.get("thumbnail") or "", raw=item, **attrs,
    )


def from_browser_record(record: dict, source: str) -> Listing:
    """Convierte el formato comun exportado por el navegador en un Listing."""
    return Listing(
        item_id=str(record.get("item_id") or record.get("id") or record.get("url") or ""),
        title=str(record.get("title") or ""),
        url=str(record.get("url") or ""),
        price=float(record.get("price") or 0),
        currency=str(record.get("currency") or "USD"),
        neighborhood=str(record.get("neighborhood") or ""),
        source=source,
        address=str(record.get("address") or ""),
        latitude=number(record.get("latitude")),
        longitude=number(record.get("longitude")),
        rooms=number(record.get("rooms")),
        bedrooms=number(record.get("bedrooms")),
        covered_m2=number(record.get("covered_m2")),
        total_m2=number(record.get("total_m2")),
        parking=number(record.get("parking")),
        description=str(record.get("description") or ""),
        thumbnail=str(record.get("thumbnail") or ""),
        raw=record,
    )
