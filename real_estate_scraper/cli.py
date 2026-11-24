import argparse
from pathlib import Path
import sys

from .browser_import import load_browser_export
from .config import load_config
from .dedupe import deduplicate
from .demo import DEMO_ITEMS
from .evaluate import evaluate, rank
from .normalize import from_api, plain
from .report import write_reports
from .storage import add_previous_prices, save
from .web import MercadoLibreWebScraper


def main() -> None:
    parser = argparse.ArgumentParser(description="Busca oportunidades de departamentos")
    parser.add_argument("command", choices=("run", "demo"), nargs="?", default="run")
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--browser-export", default=None)
    args = parser.parse_args()
    root = Path.cwd()
    config = load_config(root / args.config)
    if args.command == "demo":
        raw_items = DEMO_ITEMS
        listings = [from_api(item) for item in raw_items]
    else:
        search = config["search"]
        scraper = MercadoLibreWebScraper(search["request_delay_seconds"])
        req = config["requirements"]
        listings = []
        warnings: list[str] = []
        mercado_libre_ok = False
        try:
            mercado_libre = scraper.search(search["url"], search["max_pages"], search["page_size"], req.neighborhoods)
            if not mercado_libre:
                raise RuntimeError("la busqueda devolvio 0 publicaciones")
            scraper.enrich_candidates(mercado_libre, req.min_total_m2, req.min_price_usd, req.max_price_usd)
            listings.extend(mercado_libre)
            mercado_libre_ok = True
        except RuntimeError as exc:
            warnings.append(f"Mercado Libre: {exc}")
        browser_path = Path(args.browser_export or config.get("browser", {}).get("export_file", "data/browser_sources.json"))
        if not browser_path.is_absolute():
            browser_path = root / browser_path
        browser_listings, browser_warnings = load_browser_export(
            browser_path, float(config.get("browser", {}).get("max_age_hours", 30)), req.neighborhoods
        )
        browser_mercado_libre = [item for item in browser_listings if item.source == "mercadolibre"]
        browser_other = [item for item in browser_listings if item.source != "mercadolibre"]
        if mercado_libre_ok:
            listings.extend(browser_other)
        elif browser_mercado_libre:
            scraper.enrich_candidates(
                browser_mercado_libre, req.min_total_m2, req.min_price_usd, req.max_price_usd
            )
            listings.extend(browser_mercado_libre)
            listings.extend(browser_other)
            mercado_libre_ok = True
            warnings.append(
                f"Mercado Libre: se utilizo la recoleccion del navegador ({len(browser_mercado_libre)} publicaciones)"
            )
        warnings.extend(browser_warnings)
        for warning in warnings:
            print(f"Aviso: {warning}", file=sys.stderr)
        if not mercado_libre_ok:
            print(
                "Error: la corrida quedo incompleta porque Mercado Libre no pudo aportar publicaciones; "
                "se conserva el ultimo reporte completo",
                file=sys.stderr,
            )
            raise SystemExit(2)
        if not listings:
            print("Error: ninguna fuente pudo aportar publicaciones", file=sys.stderr)
            raise SystemExit(2)
    # Las oficinas aparecen ocasionalmente en resultados de departamentos.
    # Se excluyen antes de agrupar y evaluar para que no formen parte del reporte.
    listings = [item for item in listings if "oficina" not in plain(item.title)]
    listings = deduplicate(listings)
    req = config["requirements"]
    prefs = config["preferences"]
    listings = [evaluate(item, req, prefs["corridor_terms"], prefs["renovation_terms"]) for item in listings]
    listings = rank(listings)
    out = root / config["output"]["directory"]
    add_previous_prices(out / "listings.db", listings)
    save(out / "listings.db", listings)
    html_path, csv_path, snapshot_path = write_reports(out, listings)
    matches = sum(x.status == "match" for x in listings)
    review = sum(x.status == "review" for x in listings)
    duplicates = sum(max(0, x.duplicate_count - 1) for x in listings)
    sources = sorted({source for item in listings for source in (item.source_ids or {item.source: item.item_id})})
    print(f"Propiedades unicas: {len(listings)} | duplicados agrupados: {duplicates} | coincidencias: {matches} | para revisar: {review}")
    print(f"Fuentes: {', '.join(sources)}")
    print(f"Reporte: {html_path.resolve()}\nCoincidencias CSV: {csv_path.resolve()}\nSnapshot: {snapshot_path.resolve()}")
