/* Extractores de solo lectura para ejecutar dentro del navegador de Codex. */

export function extractMercadoLibre() {
  const metric = (text, pattern = /[\d.]+(?:,[\d]+)?/) => {
    const match = String(text || "").match(pattern);
    if (!match) return null;
    const value = String(match[1] ?? match[0]).replace(/\./g, "").replace(",", ".");
    return Number(value);
  };
  return Array.from(document.querySelectorAll("li.ui-search-layout__item")).map((card) => {
    const anchor = card.querySelector("a.poly-component__title");
    const href = anchor ? anchor.href : "";
    const idMatch = href.match(/MLA-(\d+)/);
    const title = ((anchor && anchor.textContent) || "").trim();
    const attributes = Array.from(card.querySelectorAll("li.poly-attributes_list__item"))
      .map((node) => (node.textContent || "").trim());
    const attributeText = attributes.join(" | ");
    const location = (card.querySelector(".poly-component__location")?.textContent || "").trim();
    const fraction = (card.querySelector(".andes-money-amount__fraction")?.textContent || "").trim();
    const currencySymbol = (card.querySelector(".andes-money-amount__currency-symbol")?.textContent || "").trim();
    const image = card.querySelector("img");
    return {
      item_id: idMatch ? idMatch[1] : "",
      title,
      url: href.split("#", 1)[0],
      price: metric(fraction) || 0,
      currency: /US\$|USD/i.test(currencySymbol) ? "USD" : currencySymbol,
      neighborhood: location,
      address: location,
      rooms: metric(attributeText, /([\d.,]+)\s*ambs?\.?/i),
      bedrooms: metric(attributeText, /([\d.,]+)\s*dorm(?:itorios?)?\.?/i),
      bathrooms: metric(attributeText, /([\d.,]+)\s*ba(?:n|ñ)os?\.?/i),
      covered_m2: metric(attributeText, /([\d.,]+)\s*m²\s*cubiertos?/i),
      total_m2: metric(attributeText, /([\d.,]+)\s*m²\s*totales?/i),
      parking: 1,
      description: (card.innerText || "").trim().slice(0, 2000),
      thumbnail: image ? image.currentSrc || image.src || "" : ""
    };
  }).filter((item) => item.item_id && item.url && item.price);
}

export function extractZonaprop() {
  const absolute = (href) => new URL(href, location.origin).href.split("?", 1)[0];
  const amount = (text) => {
    const match = String(text || "").match(/USD\s*([\d.]+)/i);
    return match ? Number(match[1].replace(/\./g, "")) : 0;
  };
  const metric = (text, pattern) => {
    const match = String(text || "").match(pattern);
    return match ? Number(match[1].replace(".", "").replace(",", ".")) : null;
  };
  const cards = Array.from(document.querySelectorAll('[class*="postingCardLayout-module__posting-card-layout"]'));
  return cards.map((card) => {
    const anchor = card.querySelector('a[href*="/propiedades/clasificado/"]');
    const href = anchor ? absolute(anchor.getAttribute("href")) : "";
    const text = card.innerText || "";
    const image = card.querySelector('img[alt^="Departamento"]') || card.querySelector("img");
    const alt = image ? image.getAttribute("alt") || "" : "";
    const headings = Array.from(card.querySelectorAll("h4")).map((node) => (node.innerText || "").trim()).filter(Boolean);
    const altParts = alt.split(" · ").map((part) => part.trim()).filter(Boolean);
    const title = altParts.length > 4 ? altParts.slice(4).join(" · ") : ((anchor && anchor.innerText) || "").trim().slice(0, 240);
    const description = ((anchor && anchor.innerText) || "").trim();
    const idMatch = href.match(/-(\d+)\.html$/);
    const covered = metric(alt, /Departamento\s*·\s*([\d.,]+)\s*(?:m²|ha)/i);
    return {
      item_id: idMatch ? idMatch[1] : href,
      title,
      url: href,
      price: amount(text),
      currency: "USD",
      neighborhood: headings[1] || "",
      address: headings[0] || "",
      rooms: metric(text, /([\d.,]+)\s*amb\./i),
      bedrooms: metric(text, /([\d.,]+)\s*dorm\./i),
      bathrooms: metric(text, /([\d.,]+)\s*ba(?:n|ñ)os?\./i),
      covered_m2: covered,
      total_m2: metric(text, /([\d.,]+)\s*m²\s*tot\./i) ?? metric(description, /([\d.,]+)\s*m²?\s*totales?/i),
      parking: metric(text, /([\d.,]+)\s*coch\./i),
      description,
      thumbnail: image ? image.getAttribute("src") || "" : ""
    };
  }).filter((item) => item.url && item.price);
}

export function extractArgenprop() {
  const absolute = (href) => new URL(href, location.origin).href.split("?", 1)[0];
  const amount = (text) => {
    const match = String(text || "").match(/USD\s*([\d.]+)/i);
    return match ? Number(match[1].replace(/\./g, "")) : 0;
  };
  const metric = (text, pattern) => {
    const match = String(text || "").match(pattern);
    return match ? Number(match[1].replace(".", "").replace(",", ".")) : null;
  };
  return Array.from(document.querySelectorAll("a.card")).map((card) => {
    const href = absolute(card.getAttribute("href") || "");
    const text = card.innerText || "";
    const lines = text.split("\n").map((line) => line.trim()).filter(Boolean);
    const locationIndex = lines.findIndex((line) => /^Departamento en Venta en /i.test(line));
    const locationLine = locationIndex >= 0 ? lines[locationIndex] : "";
    const neighborhoodMatch = locationLine.match(/^Departamento en Venta en ([^,]+)/i);
    const images = Array.from(card.querySelectorAll("img"));
    const alts = images.map((image) => image.getAttribute("alt") || "").join("\n");
    const hrefId = href.match(/--(\d+)$/);
    const roomsFromUrl = href.match(/-(\d+)-ambientes--/);
    const paragraphs = Array.from(card.querySelectorAll("p")).map((node) => (node.innerText || "").trim()).filter(Boolean);
    const description = paragraphs.sort((a, b) => b.length - a.length)[0] || "";
    const summedTotal = description.match(/([\d.,]+)\s*m\s*\+\s*([\d.,]+)\s*m/i);
    return {
      item_id: hrefId ? hrefId[1] : href,
      title: ((card.querySelector("h2") || {}).innerText || "").trim(),
      url: href,
      price: amount(text),
      currency: "USD",
      neighborhood: neighborhoodMatch ? neighborhoodMatch[1] : "",
      address: locationIndex > 0 ? lines[locationIndex - 1] : "",
      rooms: roomsFromUrl ? Number(roomsFromUrl[1]) : null,
      bedrooms: metric(text, /([\d.,]+)\s*dorm\./i),
      bathrooms: metric(text, /([\d.,]+)\s*ba(?:n|ñ)os?\./i),
      covered_m2: metric(text, /([\d.,]+)\s*m²\s*cubie\./i),
      total_m2: summedTotal ? metric(summedTotal[1], /([\d.,]+)/) + metric(summedTotal[2], /([\d.,]+)/) : metric(description, /([\d.,]+)\s*m²?\s*totales?/i),
      parking: metric(alts + "\n" + description, /(?:con\s*)?([\d.,]+)\s*cocheras?/i),
      description,
      thumbnail: images.length ? images[0].getAttribute("src") || "" : ""
    };
  }).filter((item) => item.url && item.price);
}
