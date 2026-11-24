from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

from real_estate_scraper.cli import main
from real_estate_scraper.config import Requirements
from real_estate_scraper.models import Listing


class CliTests(unittest.TestCase):
    @patch("real_estate_scraper.cli.write_reports")
    @patch("real_estate_scraper.cli.load_browser_export")
    @patch("real_estate_scraper.cli.MercadoLibreWebScraper")
    @patch("real_estate_scraper.cli.load_config")
    def test_does_not_write_partial_report_when_mercado_libre_fails(
        self, load_config, scraper_class, load_browser_export, write_reports
    ):
        load_config.return_value = {
            "search": {
                "url": "https://example.test/search",
                "max_pages": 1,
                "page_size": 48,
                "request_delay_seconds": 0,
            },
            "browser": {"export_file": "data/browser_sources.json", "max_age_hours": 30},
            "requirements": Requirements(20000, 200000, 3, 80, 1, 2, ("Belgrano",)),
            "preferences": {"corridor_terms": [], "renovation_terms": []},
            "output": {"directory": "data"},
        }
        scraper = Mock()
        scraper.search.side_effect = RuntimeError("fallo DNS")
        scraper_class.return_value = scraper
        load_browser_export.return_value = (
            [Listing("Z1", "Depto", "https://z/1", 140000, "USD", "Belgrano", source="zonaprop")],
            [],
        )

        with patch.object(sys, "argv", ["real-estate-scraper", "run"]), patch(
            "real_estate_scraper.cli.Path.cwd", return_value=Path("/tmp/project")
        ):
            with self.assertRaisesRegex(SystemExit, "2"):
                main()

        write_reports.assert_not_called()

    @patch("real_estate_scraper.cli.write_reports")
    @patch("real_estate_scraper.cli.save")
    @patch("real_estate_scraper.cli.add_previous_prices")
    @patch("real_estate_scraper.cli.load_browser_export")
    @patch("real_estate_scraper.cli.MercadoLibreWebScraper")
    @patch("real_estate_scraper.cli.load_config")
    def test_uses_browser_fallback_when_http_search_is_empty(
        self, load_config, scraper_class, load_browser_export, add_previous_prices, save, write_reports
    ):
        load_config.return_value = {
            "search": {
                "url": "https://example.test/search",
                "max_pages": 1,
                "page_size": 48,
                "request_delay_seconds": 0,
            },
            "browser": {"export_file": "data/browser_sources.json", "max_age_hours": 30},
            "requirements": Requirements(20000, 200000, 3, 80, 1, 2, ("Belgrano",)),
            "preferences": {"corridor_terms": [], "renovation_terms": []},
            "output": {"directory": "data"},
        }
        scraper = Mock()
        scraper.search.return_value = []
        scraper_class.return_value = scraper
        browser_listing = Listing(
            "M1", "Depto", "https://m/1", 140000, "USD", "Belgrano", source="mercadolibre",
            rooms=3, bedrooms=2, bathrooms=2, covered_m2=90, total_m2=95, parking=1,
        )
        load_browser_export.return_value = ([browser_listing], [])
        write_reports.return_value = (Path("report.html"), Path("matches.csv"), Path("snapshot.csv"))

        with patch.object(sys, "argv", ["real-estate-scraper", "run"]), patch(
            "real_estate_scraper.cli.Path.cwd", return_value=Path("/tmp/project")
        ):
            main()

        scraper.enrich_candidates.assert_called_once()
        save.assert_called_once()
        write_reports.assert_called_once()


if __name__ == "__main__":
    unittest.main()
