import { norm, haversineKm, extractContacts, hash } from './lib.js';
import { TOWNS } from './towns.js';

const has = (nt, words) => words.filter((w) => new RegExp(`\\b${norm(w)}`).test(nt));

/** Turn a raw {title,snippet,url,source} into a scored offer, or null if irrelevant. */
export function classify(raw, cfg) {
  const text = `${raw.title} ${raw.snippet}`;
  const nt = norm(text);
  const instruments = has(nt, cfg.instruments);
  const events = has(nt, cfg.events);
  if (!instruments.length) return null;
  // Strictly-musician words alone (e.g. "musico") need an event context to avoid noise.
  const core = instruments.some((i) => /piano|violin|teclado/.test(norm(i)));
  if (!events.length && !core) return null;

  const demand = has(nt, cfg.demandWords).length;
  const advert = has(nt, cfg.advertWords).length;
  const kind = demand > advert ? 'demand' : advert > demand ? 'advert' : 'unknown';

  // Location
  const origin = cfg.location;
  let town = '', dist = null;
  if (raw.lat != null && raw.lon != null) {
    dist = Math.round(haversineKm(origin, raw));
  } else {
    let best = null;
    for (const t of TOWNS) {
      if (new RegExp(`\\b${norm(t.name)}\\b`).test(nt)) {
        const d = haversineKm(origin, t);
        // prefer the most specific (longest) town name, e.g. "Puerto de Sagunto" over "Sagunto"
        if (!best || t.name.length > best.t.name.length) best = { t, d };
      }
    }
    if (best) { town = best.t.name; dist = Math.round(best.d); }
  }
  if (dist != null && dist > cfg.location.radiusKm) return null; // clearly outside area

  let score = 0;
  score += core ? 3 : 1;
  score += Math.min(events.length, 3);
  score += kind === 'demand' ? 4 : kind === 'advert' ? -4 : 0;
  score += dist != null ? 2 : 0;
  if (/(bodas?\.net|cronoshare|milanuncios|wallapop|facebook)/.test(raw.url)) score += 1;

  return {
    id: hash(raw.url.replace(/[?#].*$/, '') || raw.title),
    title: raw.title.slice(0, 200),
    snippet: raw.snippet.slice(0, 500),
    url: raw.url,
    source: raw.source,
    postedAt: raw.date ? safeDate(raw.date) : '',
    instruments: [...new Set(instruments.map(norm))],
    events: [...new Set(events.map(norm))],
    kind, town, distKm: dist, score,
    contact: extractContacts(text),
  };
}

function safeDate(d) {
  const t = new Date(d);
  return isNaN(t) ? '' : t.toISOString();
}
