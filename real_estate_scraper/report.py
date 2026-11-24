from __future__ import annotations

import csv
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
import json

from .models import Listing


CSS = '''
:root{
  --cream:#faf4e8; --paper:#fffdf8; --ink:#231b12; --ink-soft:#5c5142;
  --forest:#1f3d2f; --forest-light:#2e5745; --terracotta:#c15a34; --terracotta-light:#e08a5f;
  --gold:#c99a3f; --line:#e7dcc6; --shadow:0 10px 30px -12px rgba(35,27,18,.25);
  color-scheme: light;
}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--ink);font:400 16px/1.5 "Work Sans",sans-serif;
  background-image:radial-gradient(circle at 10% 0%, rgba(201,154,63,.12), transparent 45%),
    radial-gradient(circle at 90% 10%, rgba(193,90,52,.10), transparent 40%);}
a{color:var(--forest)}
h1,h2,h3{font-family:"Fraunces",serif;font-weight:600;margin:0}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px 80px}
.hero{padding:48px 20px 28px;text-align:center}
.hero .eyebrow{letter-spacing:.14em;text-transform:uppercase;font-size:12px;color:var(--terracotta);font-weight:600}
.hero h1{font-size:clamp(34px,6vw,54px);margin:6px 0 10px;color:var(--forest)}
.hero p.sub{color:var(--ink-soft);font-size:16px;margin:0 auto;max-width:520px}
.chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:22px 0 0}
.chip{background:var(--paper);border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-size:13px;color:var(--forest);font-weight:500}
.stats{display:flex;gap:28px;justify-content:center;margin:30px 0 0;flex-wrap:wrap}
.stat{text-align:center}
.stat b{display:block;font-family:"Fraunces",serif;font-size:30px;color:var(--terracotta)}
.stat span{font-size:12px;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.08em}
.controls{position:sticky;top:0;z-index:5;background:rgba(250,244,232,.92);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line);padding:14px 20px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:34px -20px 0}
.controls select, .controls button{font:500 13px "Work Sans",sans-serif;padding:9px 14px;border-radius:10px;border:1px solid var(--line);background:var(--paper);color:var(--ink)}
.controls button{cursor:pointer;transition:background .15s}
.controls button.active{background:var(--forest);color:#fff;border-color:var(--forest)}
.controls .count{margin-left:auto;font-size:13px;color:var(--ink-soft)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px;margin-top:24px}
article.card{background:var(--paper);border-radius:18px;overflow:hidden;box-shadow:var(--shadow);
  display:flex;flex-direction:column;border:1px solid var(--line);position:relative;animation:rise .5s ease backwards}
article.card .thumb{position:relative;aspect-ratio:4/3;background:#ddd2b8}
article.card .thumb img{width:100%;height:100%;object-fit:cover;display:block}
.score{position:absolute;top:10px;left:10px;background:var(--forest);color:#fff;font-family:"Fraunces",serif;
  font-weight:700;font-size:15px;border-radius:999px;padding:5px 11px;box-shadow:0 4px 10px rgba(0,0,0,.25)}
.score.mid{background:var(--gold)}
.score.low{background:var(--terracotta)}
.fav{position:absolute;top:8px;right:8px;width:34px;height:34px;border-radius:50%;border:none;
  background:rgba(255,253,248,.9);font-size:17px;cursor:pointer;display:flex;align-items:center;justify-content:center;
  box-shadow:0 2px 8px rgba(0,0,0,.2)}
.fav.on{background:var(--terracotta);color:#fff}
.body{padding:16px 18px 18px;display:flex;flex-direction:column;gap:8px;flex:1}
.body h2{font-size:17px;line-height:1.3}
.body h2 a{color:var(--ink);text-decoration:none}
.body h2 a:hover{color:var(--terracotta)}
.price-row{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.price{font-family:"Fraunces",serif;font-size:22px;font-weight:700;color:var(--terracotta)}
.permsq{font-size:12px;color:var(--ink-soft)}
.badges{display:flex;flex-wrap:wrap;gap:6px}
.badge{background:var(--cream);border:1px solid var(--line);border-radius:8px;padding:4px 9px;font-size:12px;color:var(--ink-soft)}
.median{font-size:12px;color:var(--ink-soft);margin-top:auto}
.sources{font-size:12px}
.near-toggle{margin:40px 0 0;text-align:center}
.near-toggle button{font:600 13px "Work Sans",sans-serif;background:none;border:1px solid var(--line);
  border-radius:999px;padding:10px 20px;cursor:pointer;color:var(--forest)}
.near-section{display:none;margin-top:18px}
.near-section.open{display:block}
.near-section h3{font-size:20px;color:var(--ink-soft);margin:0 0 4px}
.near-section .hint{color:var(--ink-soft);font-size:13px;margin:0 0 16px}
article.near{display:flex;gap:14px;background:var(--paper);border:1px dashed var(--line);border-radius:14px;
  padding:12px;margin-bottom:10px;opacity:.85}
article.near img{width:100px;height:76px;object-fit:cover;border-radius:8px;background:#ddd;flex:none}
article.near h4{font-size:14px;margin:0 0 3px;font-family:"Work Sans",sans-serif;font-weight:600}
article.near .reasons{color:var(--terracotta-light);font-size:12px}
.empty{text-align:center;padding:60px 20px;color:var(--ink-soft)}
footer{text-align:center;color:var(--ink-soft);font-size:12px;margin-top:60px;padding-top:20px;border-top:1px solid var(--line)}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
[hidden]{display:none!important}
'''


def _score_class(score: float) -> str:
    if score >= 70:
        return ""
    if score >= 50:
        return "mid"
    return "low"


def _card_html(x: Listing, index: int) -> str:
    sources = " · ".join(
        f'<a href="{escape(url)}">{escape(source)}</a>' for source, url in sorted(x.source_urls.items())
    )
    bedrooms = f'<span class="badge">{x.bedrooms:g} dorm</span>' if x.bedrooms is not None else ""
    covered = f'<span class="badge">{x.covered_m2:g} m² cub</span>' if x.covered_m2 is not None else ""
    median = (
        f'<p class="median">Mediana de esta corrida en el barrio: {x.neighborhood_median:,.0f} USD/m²</p>'
        if x.neighborhood_median else ""
    )
    key = escape(x.property_key or x.item_id, quote=True)
    delay = min(index, 10) * 0.05
    return f'''<article class="card" data-key="{key}" data-score="{x.opportunity_score}" data-price="{x.price}"
  data-m2="{x.total_m2}" data-barrio="{escape(x.neighborhood, quote=True)}" style="animation-delay:{delay:.2f}s">
  <div class="thumb"><img src="{escape(x.thumbnail)}" alt="" loading="lazy">
    <span class="score {_score_class(x.opportunity_score)}">{x.opportunity_score:.0f}</span>
    <button class="fav" data-fav-for="{key}" aria-label="Marcar favorito" onclick="toggleFav(this)">&#9825;</button>
  </div>
  <div class="body">
    <h2><a href="{escape(x.url)}" target="_blank" rel="noopener">{escape(x.title)}</a></h2>
    <div class="price-row"><span class="price">USD {x.price:,.0f}</span><span class="permsq">{x.usd_per_m2:,.0f} USD/m²</span></div>
    <div class="badges"><span class="badge">{escape(x.neighborhood)}</span><span class="badge">{x.rooms:g} amb</span>{bedrooms}{covered}<span class="badge">{x.total_m2:g} m² total</span><span class="badge">{x.parking:g} cochera(s)</span></div>
    {median}
    <p class="sources">Fuentes: {sources}</p>
  </div>
</article>'''


def _near_card_html(x: Listing) -> str:
    known = " · ".join(filter(None, [
        f"{x.rooms:g} amb" if x.rooms is not None else "",
        f"{x.total_m2:g} m² total" if x.total_m2 is not None else "cubiertos no informados",
    ]))
    return f'''<article class="near"><img src="{escape(x.thumbnail)}" alt="">
  <div><h4><a href="{escape(x.url)}" target="_blank" rel="noopener">{escape(x.title)}</a></h4>
  <p>USD {x.price:,.0f} · {escape(x.neighborhood)} · {escape(known)}</p>
  <p class="reasons">No cumple: {escape('; '.join(x.reasons))}</p></div></article>'''


SCRIPT = '''
(function(){
  var FAV_KEY = "depto-favoritos";
  function favs(){ try { return JSON.parse(localStorage.getItem(FAV_KEY) || "[]"); } catch(e){ return []; } }
  function saveFavs(list){ try { localStorage.setItem(FAV_KEY, JSON.stringify(list)); } catch(e){} }
  window.toggleFav = function(btn){
    var key = btn.getAttribute("data-fav-for");
    var list = favs();
    var i = list.indexOf(key);
    if (i === -1) { list.push(key); btn.classList.add("on"); btn.innerHTML = "&#9829;"; }
    else { list.splice(i, 1); btn.classList.remove("on"); btn.innerHTML = "&#9825;"; }
    saveFavs(list);
    applyFilters();
  };
  function paintFavs(){
    var list = favs();
    document.querySelectorAll(".fav").forEach(function(btn){
      var on = list.indexOf(btn.getAttribute("data-fav-for")) !== -1;
      btn.classList.toggle("on", on);
      btn.innerHTML = on ? "&#9829;" : "&#9825;";
    });
  }
  function cards(){ return Array.prototype.slice.call(document.querySelectorAll("#grid .card")); }
  function applySort(){
    var mode = document.getElementById("sortSelect").value;
    var grid = document.getElementById("grid");
    var list = cards();
    list.sort(function(a, b){
      if (mode === "price-asc") return a.dataset.price - b.dataset.price;
      if (mode === "price-desc") return b.dataset.price - a.dataset.price;
      if (mode === "m2-desc") return b.dataset.m2 - a.dataset.m2;
      return b.dataset.score - a.dataset.score;
    });
    list.forEach(function(el){ grid.appendChild(el); });
  }
  function applyFilters(){
    var barrio = document.getElementById("barrioSelect").value;
    var onlyFav = document.getElementById("favToggle").classList.contains("active");
    var list = favs();
    var visible = 0;
    cards().forEach(function(card){
      var matchesBarrio = barrio === "" || card.dataset.barrio === barrio;
      var matchesFav = !onlyFav || list.indexOf(card.dataset.key) !== -1;
      var show = matchesBarrio && matchesFav;
      card.hidden = !show;
      if (show) visible++;
    });
    document.getElementById("visibleCount").textContent = visible;
  }
  document.getElementById("sortSelect").addEventListener("change", applySort);
  document.getElementById("barrioSelect").addEventListener("change", applyFilters);
  document.getElementById("favToggle").addEventListener("click", function(){
    this.classList.toggle("active");
    applyFilters();
  });
  var nearBtn = document.getElementById("nearToggle");
  if (nearBtn) {
    nearBtn.addEventListener("click", function(){
      var section = document.getElementById("nearSection");
      var open = section.classList.toggle("open");
      this.textContent = open ? "Ocultar más cercanos" : this.dataset.label;
    });
  }
  paintFavs();
  applySort();
  applyFilters();
})();
'''


def write_reports(directory: Path, listings: list[Listing]) -> tuple[Path, Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    matches = [x for x in listings if x.status == "match"]
    csv_path = directory / "matches.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["score", "precio_usd", "usd_m2", "barrio", "ambientes", "dormitorios", "cubiertos_m2", "total_m2", "cocheras", "titulo", "url", "fuentes", "property_key"])
        for x in matches:
            writer.writerow([x.opportunity_score, x.price, round(x.usd_per_m2 or 0), x.neighborhood, x.rooms, x.bedrooms, x.covered_m2, x.total_m2, x.parking, x.title, x.url, ", ".join(sorted(x.source_ids)), x.property_key])
    snapshot_path = directory / "snapshot.csv"
    observed_at = datetime.now().astimezone().replace(microsecond=0)
    with snapshot_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "observado_el", "item_id", "estado", "puntaje", "precio_usd",
            "precio_anterior_usd", "cambio_precio_usd", "cambio_precio_pct",
            "usd_m2", "barrio", "direccion", "ambientes", "dormitorios",
            "cubiertos_m2", "total_m2", "cocheras", "titulo", "url", "motivos",
            "fuente", "property_key", "fuentes", "enlaces_fuentes", "duplicados",
        ])
        for x in listings:
            writer.writerow([
                observed_at.isoformat(), x.item_id, x.status, x.opportunity_score or "", x.price,
                x.previous_price_usd if x.previous_price_usd is not None else "",
                x.price_change_usd if x.price_change_usd is not None else "",
                x.price_change_percent if x.price_change_percent is not None else "",
                x.usd_per_m2 if x.usd_per_m2 is not None else "",
                x.neighborhood, x.address, x.rooms if x.rooms is not None else "",
                x.bedrooms if x.bedrooms is not None else "",
                x.covered_m2 if x.covered_m2 is not None else "",
                x.total_m2 if x.total_m2 is not None else "",
                x.parking if x.parking is not None else "", x.title, x.url,
                "; ".join(x.reasons),
                x.source, x.property_key, ", ".join(sorted(x.source_ids or {x.source: x.item_id})),
                json.dumps(x.source_urls or {x.source: x.url}, ensure_ascii=False, sort_keys=True),
                x.duplicate_count,
            ])

    matches_sorted = sorted(matches, key=lambda x: x.opportunity_score, reverse=True)
    cards_html = "".join(_card_html(x, i) for i, x in enumerate(matches_sorted))
    neighborhoods = sorted({x.neighborhood for x in matches if x.neighborhood})
    barrio_options = "".join(
        f'<option value="{escape(n, quote=True)}">{escape(n)}</option>' for n in neighborhoods
    )

    near = [x for x in listings if x.status == "rejected" and x.currency == "USD" and 1 <= x.price <= 200000]
    near.sort(key=lambda x: (x.total_m2 or 0, x.covered_m2 or 0), reverse=True)
    near_cards_html = "".join(_near_card_html(x) for x in near[:10])

    next_run = (observed_at + timedelta(days=2)).strftime("%d/%m")
    observed_label = observed_at.strftime("%d/%m/%Y %H:%M")

    if cards_html:
        grid_section = f'<div id="grid" class="grid">{cards_html}</div>'
    else:
        grid_section = '<p class="empty">No hubo coincidencias confirmadas en esta corrida. Volvé en 2 días.</p>'

    near_block = ""
    if near_cards_html:
        near_block = f'''<div class="near-toggle">
  <button id="nearToggle" data-label="Ver también más cercanos ({len(near)})">Ver también más cercanos ({len(near)})</button>
</div>
<div id="nearSection" class="near-section">
  <h3>Más cercanos por superficie</h3>
  <p class="hint">No cumplen todos los mínimos; sirven para entender el mercado.</p>
  {near_cards_html}
</div>'''

    html = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Depto en la mira</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Work+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="hero">
  <div class="eyebrow">Capital Federal · actualizado cada 2 días</div>
  <h1>Depto en la mira</h1>
  <p class="sub">Búsqueda automática de 3+ ambientes, 80+ m² totales y cochera, hasta USD 200.000.</p>
  <div class="chips">
    <span class="chip">Hasta USD 200.000</span>
    <span class="chip">3+ ambientes</span>
    <span class="chip">80+ m² totales</span>
    <span class="chip">1+ cochera</span>
    <span class="chip">Palermo · Belgrano · Núñez · Recoleta y alrededores</span>
  </div>
  <div class="stats">
    <div class="stat"><b>{len(matches)}</b><span>Coincidencias</span></div>
    <div class="stat"><b>{len(listings)}</b><span>Avisos analizados</span></div>
    <div class="stat"><b>{observed_label}</b><span>Última corrida</span></div>
    <div class="stat"><b>{next_run}</b><span>Próxima actualización</span></div>
  </div>
</div>
<div class="wrap">
  <div class="controls">
    <select id="sortSelect">
      <option value="score">Ordenar: puntaje</option>
      <option value="price-asc">Precio: menor a mayor</option>
      <option value="price-desc">Precio: mayor a menor</option>
      <option value="m2-desc">Más m² totales</option>
    </select>
    <select id="barrioSelect">
      <option value="">Todos los barrios</option>
      {barrio_options}
    </select>
    <button id="favToggle">&#9825; Solo favoritos</button>
    <span class="count"><span id="visibleCount">{len(matches)}</span> mostrados</span>
  </div>
  {grid_section}
  {near_block}
  <footer>
    El HTML y los precios publicados por los vendedores pueden cambiar o tener errores.
    Verificá precio, superficie y cochera en el aviso original antes de decidir. Generado el {observed_label}.
  </footer>
</div>
<script>{SCRIPT}</script>
</body>
</html>'''
    html_path = directory / "report.html"
    html_path.write_text(html, encoding="utf-8")
    return html_path, csv_path, snapshot_path
