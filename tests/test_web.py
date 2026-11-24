import unittest

from real_estate_scraper.web import DetailPageParser, MercadoLibreWebScraper, SearchPageParser, apply_detail, listing_from_card


SEARCH_HTML = '''<div class="poly-card"><img class="poly-component__picture" src="photo.webp"><a class="poly-component__title" href="https://departamento.mercadolibre.com.ar/MLA-123-depto-_JM#tracking">Depto amplio</a><span class="poly-price__amount" aria-label="145000 dólares"></span><ul><li class="poly-attributes_list__item">3 ambs.</li><li class="poly-attributes_list__item">88 m² cubiertos</li></ul><span class="poly-component__location">Cabildo 1000, Belgrano, Capital Federal</span></div>'''
DETAIL_HTML = '''<table><tr><th>Superficie total</th><td>96 m²</td></tr><tr><th>Superficie cubierta</th><td>88 m²</td></tr><tr><th>Ambientes</th><td>3</td></tr><tr><th>Dormitorios</th><td>2</td></tr><tr><th>Cocheras</th><td>1</td></tr></table><div class="ui-pdp-description__content"><p>A refaccionar sobre Cabildo.</p></div>'''


class WebParserTests(unittest.TestCase):
    def test_search_card(self):
        parser = SearchPageParser()
        parser.feed(SEARCH_HTML)
        self.assertEqual(len(parser.cards), 1)
        item = listing_from_card(parser.cards[0], ("Belgrano",))
        self.assertEqual(item.item_id, "MLA123")
        self.assertEqual(item.price, 145000)
        self.assertEqual(item.covered_m2, 88)
        self.assertEqual(item.neighborhood, "Belgrano")

    def test_detail_table(self):
        parser = SearchPageParser()
        parser.feed(SEARCH_HTML)
        item = listing_from_card(parser.cards[0], ("Belgrano",))
        apply_detail(item, DETAIL_HTML)
        self.assertEqual(item.total_m2, 96)
        self.assertEqual(item.bedrooms, 2)
        self.assertEqual(item.parking, 1)
        self.assertIn("refaccionar", item.description)

    def test_second_page_url(self):
        url = "https://example.com/path/_PriceRange_1-2"
        self.assertEqual(MercadoLibreWebScraper.page_url(url, 1, 48), "https://example.com/path/_Desde_49_PriceRange_1-2")

    def test_later_page_url_is_dynamic(self):
        url = "https://example.com/path/_PriceRange_1-2"
        self.assertEqual(MercadoLibreWebScraper.page_url(url, 3, 48), "https://example.com/path/_Desde_145_PriceRange_1-2")


if __name__ == "__main__":
    unittest.main()
