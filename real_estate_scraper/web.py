from __future__ import annotations

from html.parser import HTMLParser
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .models import Listing
from .normalize import number, plain


def _classes(attrs: dict[str, str | None]) -> set[str]:
    return set((attrs.get("class") or "").split())


class SearchPageParser(HTMLParser):
    """Extrae las tarjetas visibles sin depender del JSON interno del sitio."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[dict] = []
        self.card: dict | None = None
        self.div_depth = 0
        self.capture: tuple[str, str] | None = None

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs_list)
        classes = _classes(attrs)
        if tag == "div" and "poly-card" in classes and self.card is None:
            self.card = {"title": "", "url": "", "price_label": "", "location": "", "attributes": [], "thumbnail": ""}
            self.div_depth = 1
            return
        if self.card is None:
            return
        if tag == "div":
            self.div_depth += 1
        if tag == "a" and "poly-component__title" in classes and "/MLA-" in (attrs.get("href") or ""):
            self.card["url"] = (attrs.get("href") or "").split("#", 1)[0]
            self.capture = (tag, "title")
        elif tag == "span" and "poly-price__amount" in classes:
            self.card["price_label"] = attrs.get("aria-label") or ""
        elif tag == "span" and "poly-component__location" in classes:
            self.capture = (tag, "location")
        elif tag == "li" and "poly-attributes_list__item" in classes:
            self.card["attributes"].append("")
            self.capture = (tag, "attribute")
        elif tag == "img" and "poly-component__picture" in classes:
            self.card["thumbnail"] = attrs.get("src") or ""

    def handle_data(self, data: str) -> None:
        if self.card is None or self.capture is None:
            return
        field = self.capture[1]
        if field == "attribute":
            self.card["attributes"][-1] += data
        else:
            self.card[field] += data

    def handle_endtag(self, tag: str) -> None:
        if self.card is None:
            return
        if self.capture and tag == self.capture[0]:
            self.capture = None
        if tag == "div":
            self.div_depth -= 1
            if self.div_depth == 0:
                if self.card["url"]:
                    self.cards.append(self.card)
                self.card = None


class DetailPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[str] = []
        self._row_depth = 0
        self._row_text: list[str] = []
        self.description_parts: list[str] = []
        self._description_depth = 0

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs_list)
        classes = _classes(attrs)
        if tag == "tr" and self._row_depth == 0:
            self._row_depth = 1
            self._row_text = []
        elif self._row_depth:
            self._row_depth += 1
        if "ui-pdp-description__content" in classes and not self._description_depth:
            self._description_depth = 1
        elif self._description_depth:
            self._description_depth += 1

    def handle_data(self, data: str) -> None:
        clean = " ".join(data.split())
        if clean and self._row_depth:
            self._row_text.append(clean)
        if clean and self._description_depth:
            self.description_parts.append(clean)

    def handle_endtag(self, tag: str) -> None:
        if self._row_depth:
            self._row_depth -= 1
            if self._row_depth == 0 and tag == "tr":
                self.rows.append("\n".join(self._row_text))
        if self._description_depth:
            self._description_depth -= 1


def _attribute_value(attributes: list[str], word: str) -> float | None:
    for value in attributes:
        if word in plain(value):
            return number(value)
    return None


def _item_id(url: str) -> str:
    match = re.search(r"/MLA-(\d+)", url)
    return f"MLA{match.group(1)}" if match else url


def _price(label: str) -> float:
    matches = re.findall(r"\d+", label)
    return float(matches[-1]) if matches else 0


def _neighborhood(location: str, allowed: tuple[str, ...]) -> str:
    normalized = plain(location)
    # Los nombres mas especificos deben ganar sobre Palermo/Belgrano.
    for name in sorted(allowed, key=len, reverse=True):
        if plain(name) in normalized:
            return name
    return ""


def listing_from_card(card: dict, neighborhoods: tuple[str, ...]) -> Listing:
    attrs = [" ".join(x.split()) for x in card["attributes"]]
    return Listing(
        item_id=_item_id(card["url"]), title=" ".join(card["title"].split()),
        url=card["url"], price=_price(card["price_label"]), currency="USD",
        neighborhood=_neighborhood(card["location"], neighborhoods),
        address=" ".join(card["location"].split()), thumbnail=card["thumbnail"],
        rooms=_attribute_value(attrs, "amb"),
        covered_m2=_attribute_value(attrs, "cubiert"),
        total_m2=_attribute_value(attrs, "total"),
    )


def apply_detail(listing: Listing, html: str) -> Listing:
    parser = DetailPageParser()
    parser.feed(html)
    values: dict[str, str] = {}
    for row in parser.rows:
        parts = row.split("\n", 1)
        if len(parts) == 2:
            values[plain(parts[0])] = parts[1]
    mapping = {
        "superficie total": "total_m2", "superficie cubierta": "covered_m2",
        "ambientes": "rooms", "dormitorios": "bedrooms", "cocheras": "parking",
    }
    for label, field in mapping.items():
        if label in values:
            setattr(listing, field, number(values[label]))
    listing.description = " ".join(parser.description_parts)
    return listing


class MercadoLibreWebScraper:
    def __init__(self, delay_seconds: float = 1, timeout: int = 30):
        self.delay_seconds = delay_seconds
        self.timeout = timeout

    def fetch(self, url: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36",
            "Accept-Language": "es-AR,es;q=0.9",
            "Accept": "text/html,application/xhtml+xml",
        }
        for attempt in range(3):
            try:
                with urlopen(Request(url, headers=headers), timeout=self.timeout) as response:
                    return response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            except HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise RuntimeError(f"Mercado Libre respondio HTTP {exc.code}") from exc
            except URLError as exc:
                if attempt == 2:
                    raise RuntimeError(f"No se pudo abrir Mercado Libre: {exc.reason}") from exc
            time.sleep(2**attempt)
        raise RuntimeError("No se pudo descargar la pagina")

    @staticmethod
    def page_url(base_url: str, page: int, page_size: int) -> str:
        if page == 0:
            return base_url
        parts = urlsplit(base_url)
        offset = page * page_size + 1
        path = parts.path.replace("/_", f"/_Desde_{offset}_", 1)
        return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))

    def search(self, url: str, max_pages: int, page_size: int, neighborhoods: tuple[str, ...]) -> list[Listing]:
        found: dict[str, Listing] = {}
        for page in range(max_pages):
            html = self.fetch(self.page_url(url, page, page_size))
            parser = SearchPageParser()
            parser.feed(html)
            page_items = [listing_from_card(card, neighborhoods) for card in parser.cards]
            for item in page_items:
                found[item.item_id] = item
            if len(page_items) < page_size:
                break
            time.sleep(self.delay_seconds)
        return list(found.values())

    def enrich_candidates(self, listings: list[Listing], min_total_m2: float, min_price: float, max_price: float) -> None:
        for item in listings:
            if item.currency != "USD" or not (min_price <= item.price <= max_price):
                continue
            if item.total_m2 is not None and item.total_m2 < min_total_m2:
                continue
            time.sleep(self.delay_seconds)
            apply_detail(item, self.fetch(item.url))
