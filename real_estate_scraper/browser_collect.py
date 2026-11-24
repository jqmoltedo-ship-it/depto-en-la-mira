"""Recolecta ZonaProp con un navegador real (Playwright).

Es un paso opcional: si Playwright no esta instalado o el sitio bloquea la
visita, el script no falla la corrida principal, simplemente no aporta avisos
de esta fuente para esta corrida.

Argenprop queda afuera a proposito: le muestra una pagina "confirma que sos
humano" a los navegadores automatizados, y este proyecto no intenta sortear
verificaciones anti-bot. Si Argenprop se quiere incluir, es manual: abrir la
busqueda en un navegador real y pegar `extractArgenprop()` (de
`scripts/browser_extract.mjs`) en la consola para generar `data/browser_sources.json`
a mano.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import load_config

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
COOKIE_BUTTON_LABELS = ("Aceptar todas", "Aceptar", "Entendido", "ACEPTAR")


def _extractor_script(root: Path) -> str:
    source = (root / "scripts" / "browser_extract.mjs").read_text(encoding="utf-8")
    return source.replace("export function", "function")


def _dismiss_cookie_banner(page) -> None:
    for label in COOKIE_BUTTON_LABELS:
        try:
            button = page.get_by_role("button", name=label, exact=False)
            if button.count() > 0:
                button.first.click(timeout=2000)
                return
        except Exception:
            continue


def _collect(playwright_module, url: str, extractor_js: str, call: str) -> list[dict]:
    browser = playwright_module.chromium.launch(headless=True)
    try:
        page = browser.new_page(user_agent=USER_AGENT, viewport={"width": 1366, "height": 900}, locale="es-AR")
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        _dismiss_cookie_banner(page)
        page.wait_for_timeout(1500)
        page.add_script_tag(content=extractor_js)
        return page.evaluate(call)
    finally:
        browser.close()


def main() -> None:
    root = Path.cwd()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Aviso: Playwright no esta instalado; se omite ZonaProp/Argenprop", file=sys.stderr)
        return

    config = load_config(root / "config.toml")
    extractor_js = _extractor_script(root)
    sources: dict[str, list[dict]] = {}
    errors: list[str] = []

    with sync_playwright() as playwright_module:
        for name, call in (("zonaprop", "extractZonaprop()"),):
            url = config.get(name, {}).get("url")
            if not url:
                continue
            try:
                sources[name] = _collect(playwright_module, url, extractor_js, call)
            except Exception as exc:  # defensivo: un sitio caido no debe tumbar al otro
                errors.append(f"{name}: {exc}")
                sources[name] = []

    export_file = config.get("browser", {}).get("export_file", "data/browser_sources.json")
    export_path = root / export_file
    export_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"collected_at": datetime.now(timezone.utc).isoformat(), "sources": sources}
    export_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = ", ".join(f"{name}: {len(items)}" for name, items in sources.items())
    print(f"Recoleccion de navegador: {counts}")
    for error in errors:
        print(f"Aviso: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
