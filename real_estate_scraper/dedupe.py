from __future__ import annotations

from copy import deepcopy
import hashlib
import re
from statistics import median

from .models import Listing
from .normalize import plain


def _address_parts(value: str) -> tuple[str, str, str]:
    """Devuelve calle, altura y piso normalizados, si estan informados."""
    text = plain((value or "").split(",", 1)[0])
    text = re.sub(r"\bavenida\b|\bav\.?\b", "av", text)
    text = re.sub(r"\bal\s+(\d{2,5})\b", r"\1", text)
    height = re.search(r"\b(\d{2,5})\b", text)
    floor = re.search(r"\b(?:piso|p)\s*(\d{1,2})\b", plain(value or ""))
    if not height:
        return "", "", floor.group(1) if floor else ""
    street = re.sub(r"\b\d{2,5}\b.*$", "", text)
    street = re.sub(r"[^a-z0-9]+", " ", street).strip()
    return street, height.group(1), floor.group(1) if floor else ""


def _close(a: float | None, b: float | None, absolute: float, relative: float = 0.0) -> bool | None:
    if a is None or b is None:
        return None
    return abs(a - b) <= max(absolute, min(a, b) * relative)


def _title_similarity(a: str, b: str) -> float:
    ignored = {"venta", "departamento", "depto", "ambientes", "con", "en", "oportunidad"}
    left = {x for x in re.findall(r"[a-z0-9]+", plain(a)) if len(x) > 2 and x not in ignored}
    right = {x for x in re.findall(r"[a-z0-9]+", plain(b)) if len(x) > 2 and x not in ignored}
    return len(left & right) / len(left | right) if left and right else 0.0


def _same_property(a: Listing, b: Listing) -> bool:
    if a.source == b.source:
        return False
    if a.neighborhood and b.neighborhood and plain(a.neighborhood) != plain(b.neighborhood):
        return False
    a_street, a_height, a_floor = _address_parts(a.address)
    b_street, b_height, b_floor = _address_parts(b.address)
    if not a_street or not a_height or (a_street, a_height) != (b_street, b_height):
        return False
    if a_floor and b_floor and a_floor != b_floor:
        return False

    covered = _close(a.covered_m2, b.covered_m2, 3, 0.04)
    total = _close(a.total_m2, b.total_m2, 4, 0.05)
    rooms = _close(a.rooms, b.rooms, 0)
    bedrooms = _close(a.bedrooms, b.bedrooms, 0)
    price = _close(a.price if a.currency == "USD" else None, b.price if b.currency == "USD" else None, 5000, 0.08)

    # Contradicciones estructurales conocidas impiden una union automatica.
    if covered is False or rooms is False or bedrooms is False:
        return False
    score = sum(value is True for value in (covered, total, rooms, bedrooms, price))
    if _title_similarity(a.title, b.title) >= 0.35:
        score += 1
    return covered is True and score >= 3


def _property_key(group: list[Listing]) -> str:
    candidates = []
    for item in group:
        street, height, floor = _address_parts(item.address)
        completeness = sum(value is not None for value in (item.covered_m2, item.total_m2, item.rooms, item.bedrooms))
        candidates.append((bool(street and height), completeness, item, street, height, floor))
    _, _, item, street, height, floor = max(candidates, key=lambda row: (row[0], row[1]))
    if street and height:
        values = [
            plain(item.neighborhood), street, height, floor,
            str(round(item.covered_m2 or 0)), str(round(item.rooms or 0)),
            str(round(item.bedrooms or 0)),
        ]
    else:
        values = [item.source, item.item_id]
    digest = hashlib.sha1("|".join(values).encode("utf-8")).hexdigest()[:16].upper()
    return f"PROP-{digest}"


def _best_value(group: list[Listing], field: str):
    values = [getattr(item, field) for item in group if getattr(item, field) not in (None, "")]
    if not values:
        return None
    if all(isinstance(value, (int, float)) for value in values):
        return float(median(values))
    return max(values, key=lambda value: len(str(value)))


def _merge(group: list[Listing]) -> Listing:
    usd = [item for item in group if item.currency == "USD" and item.price > 0]
    representative = min(usd or group, key=lambda item: item.price or float("inf"))
    merged = deepcopy(representative)
    for field in ("neighborhood", "address", "latitude", "longitude", "rooms", "bedrooms", "bathrooms", "covered_m2", "total_m2", "parking", "description", "thumbnail"):
        value = _best_value(group, field)
        if value not in (None, ""):
            setattr(merged, field, value)
    merged.property_key = _property_key(group)
    merged.source_ids = {item.source: item.item_id for item in group}
    merged.source_urls = {item.source: item.url for item in group}
    merged.source_prices = {item.source: item.price for item in group if item.currency == "USD"}
    merged.duplicate_count = len(group)
    merged.dedupe_confidence = "address+attributes" if len(group) > 1 else "single"
    merged.raw = {item.source: item.raw for item in group}
    return merged


def deduplicate(listings: list[Listing]) -> list[Listing]:
    """Agrupa conservadoramente avisos equivalentes de portales distintos."""
    parent = list(range(len(listings)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for left in range(len(listings)):
        for right in range(left + 1, len(listings)):
            if _same_property(listings[left], listings[right]):
                union(left, right)

    groups: dict[int, list[Listing]] = {}
    for index, item in enumerate(listings):
        groups.setdefault(find(index), []).append(item)
    return [_merge(group) for group in groups.values()]
