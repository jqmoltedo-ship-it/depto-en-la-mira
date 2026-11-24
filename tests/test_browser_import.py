import json
from pathlib import Path
import tempfile
import unittest

from real_estate_scraper.browser_import import load_browser_export


class BrowserImportTests(unittest.TestCase):
    def test_imports_multiple_sources(self):
        payload = {
            "collected_at": "2099-01-01T00:00:00+00:00",
            "sources": {
                "mercadolibre": [{"item_id": "5", "title": "Depto", "url": "https://m/5", "price": 135000}],
                "zonaprop": [{"item_id": "10", "title": "Depto", "url": "https://z/10", "price": 140000}],
                "argenprop": [{"item_id": "20", "title": "Depto", "url": "https://a/20", "price": 145000}],
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "browser.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            listings, warnings = load_browser_export(path)
        self.assertEqual(warnings, [])
        self.assertEqual([item.source for item in listings], ["mercadolibre", "zonaprop", "argenprop"])

    def test_ignores_promoted_listings_outside_requested_neighborhoods(self):
        payload = {
            "collected_at": "2099-01-01T00:00:00+00:00",
            "sources": {
                "zonaprop": [
                    {
                        "item_id": "10",
                        "title": "Depto en San Nicolas",
                        "url": "https://z/10",
                        "price": 140000,
                        "neighborhood": "San Nicolás, Capital Federal",
                    },
                    {
                        "item_id": "11",
                        "title": "Depto en Belgrano R",
                        "url": "https://z/11",
                        "price": 145000,
                        "neighborhood": "Belgrano R, Capital Federal",
                    },
                ]
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "browser.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            listings, warnings = load_browser_export(path, neighborhoods=("Belgrano", "Belgrano R"))

        self.assertEqual([item.item_id for item in listings], ["11"])
        self.assertEqual(listings[0].neighborhood, "Belgrano R")
        self.assertEqual(
            warnings,
            ["Se ignoraron 1 avisos promocionados de zonaprop por estar fuera de los barrios buscados"],
        )


if __name__ == "__main__":
    unittest.main()
