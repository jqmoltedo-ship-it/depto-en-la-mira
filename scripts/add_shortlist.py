#!/usr/bin/env python3
"""Agrega a mano un departamento visto en Instagram (u otro lado) al reporte.

Uso:
  python3 scripts/add_shortlist.py --title "3 amb en Belgrano" \
      --url "https://instagram.com/p/..." --price 185000 \
      --neighborhood Belgrano --rooms 3 --total-m2 85 --parking 1 \
      --notes "Visto en reel de @inmobiliariaXYZ"

Solo --title y --url son obligatorios; el resto es opcional y se muestra si
se informa. Cada corrida de scripts/run_and_publish.sh toma este archivo tal
cual esta, no lo modifica.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--title", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--price", type=float)
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--neighborhood")
    parser.add_argument("--rooms", type=float)
    parser.add_argument("--total-m2", type=float, dest="total_m2")
    parser.add_argument("--parking", type=float)
    parser.add_argument("--notes")
    parser.add_argument("--thumbnail")
    parser.add_argument("--path", default=str(Path(__file__).resolve().parent.parent / "shortlist.json"))
    args = parser.parse_args()

    path = Path(args.path)
    items = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    items.append({k: v for k, v in vars(args).items() if k != "path" and v is not None})
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Agregado. {path} tiene ahora {len(items)} publicacion(es) a mano.")


if __name__ == "__main__":
    main()
