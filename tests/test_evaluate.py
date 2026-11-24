import unittest
from pathlib import Path
import tempfile

from real_estate_scraper.config import Requirements
from real_estate_scraper.dedupe import deduplicate
from real_estate_scraper.demo import DEMO_ITEMS
from real_estate_scraper.evaluate import evaluate, rank
from real_estate_scraper.normalize import from_api, number
from real_estate_scraper.storage import add_previous_prices, save


REQ = Requirements(20000, 200000, 3, 80, 1, ("Palermo", "Belgrano", "Nunez", "Saavedra", "Colegiales"))


class EvaluationTests(unittest.TestCase):
    def test_parses_square_metres(self):
        self.assertEqual(number("85 m²"), 85)

    def test_valid_listing_matches(self):
        item = evaluate(from_api(DEMO_ITEMS[0]), REQ, ["cabildo"], ["refaccionar"])
        self.assertEqual(item.status, "match")

    def test_office_title_can_be_identified_for_exclusion(self):
        item = from_api({**DEMO_ITEMS[0], "title": "Oficina en venta con cochera"})
        self.assertIn("oficina", item.title.lower())

    def test_insufficient_total_area_rejected(self):
        raw = {**DEMO_ITEMS[1], "attributes": [
            a if a["id"] != "TOTAL_AREA" else {"id": "TOTAL_AREA", "value_name": "70 m²"}
            for a in DEMO_ITEMS[1]["attributes"]
        ]}
        item = evaluate(from_api(raw), REQ, [], [])
        self.assertEqual(item.status, "rejected")
        self.assertIn("m2 totales insuficiente", item.reasons)

    def test_missing_parking_requires_review(self):
        raw = {**DEMO_ITEMS[0], "attributes": [a for a in DEMO_ITEMS[0]["attributes"] if a["id"] != "PARKING_LOTS"]}
        item = evaluate(from_api(raw), REQ, [], [])
        self.assertEqual(item.status, "review")

    def test_rank_prefers_lower_price_per_m2(self):
        items = [evaluate(from_api(x), REQ, [], []) for x in (DEMO_ITEMS[0], DEMO_ITEMS[2])]
        ranked = rank(items)
        self.assertEqual(ranked[0].item_id, "DEMO3")

    def test_previous_price_is_calculated(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "history.db"
            first = from_api(DEMO_ITEMS[0])
            save(path, [first])
            newer_raw = {**DEMO_ITEMS[0], "price": 140000}
            newer = from_api(newer_raw)
            add_previous_prices(path, [newer])
            self.assertEqual(newer.previous_price_usd, 145000)
            self.assertEqual(newer.price_change_usd, -5000)

    def test_deduplicates_same_property_across_sources(self):
        first = from_api(DEMO_ITEMS[0])
        first.address = "Av. Cabildo 1000, Piso 4"
        second = from_api({**DEMO_ITEMS[0], "id": "ZP123", "permalink": "https://zonaprop.test/123"})
        second.source = "zonaprop"
        second.address = "Avenida Cabildo al 1000, Piso 4"
        merged = deduplicate([first, second])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].duplicate_count, 2)
        self.assertEqual(set(merged[0].source_ids), {"mercadolibre", "zonaprop"})

    def test_does_not_merge_different_known_floors(self):
        first = from_api(DEMO_ITEMS[0])
        first.address = "Cabildo 1000, Piso 4"
        second = from_api({**DEMO_ITEMS[0], "id": "ZP124"})
        second.source = "zonaprop"
        second.address = "Cabildo 1000, Piso 8"
        self.assertEqual(len(deduplicate([first, second])), 2)


if __name__ == "__main__":
    unittest.main()
