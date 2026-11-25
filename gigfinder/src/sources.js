import { fetchText, parseFeed, sleep, decodeEntities } from './lib.js';

const log = (...a) => console.log('[source]', ...a);

/** Bing RSS search: one request per (site, phrase). Reaches Facebook public posts, Milanuncios, Wallapop, Bodas.net, etc. */
export async function searchEngineSource(cfg, report) {
  const out = [];
  const queries = [];
  for (const site of cfg.sites)
    for (const phrase of cfg.searchPhrases.slice(0, 3))
      queries.push({ site, q: `site:${site} ${phrase} ${cfg.regionWords[0]}` });
  // Un-sited queries across all the web, per region
  for (const phrase of cfg.searchPhrases)
    for (const region of cfg.regionWords) queries.push({ site: 'web', q: `${phrase} ${region}` });

  let ok = 0, fail = 0;
  for (const { site, q } of queries) {
    try {
      const xml = await fetchText(`https://www.bing.com/search?format=rss&setlang=es&cc=ES&q=${encodeURIComponent(q)}`);
      for (const it of parseFeed(xml)) out.push({ ...it, source: site === 'web' ? hostOf(it.url) : site });
      ok++;
    } catch (e) {
      fail++;
      if (fail <= 3) log('bing failed:', q, e.message);
    }
    await sleep(cfg.searchDelayMs);
  }
  report.search = { queries: queries.length, ok, fail };
  return out;
}

/** User-provided RSS/Atom feeds (e.g. Google Alerts feeds, forum feeds). */
export async function rssSource(cfg, report) {
  const out = [];
  let ok = 0, fail = 0;
  for (const url of cfg.rssFeeds || []) {
    try {
      for (const it of parseFeed(await fetchText(url))) out.push({ ...it, source: hostOf(it.url) || 'rss' });
      ok++;
    } catch (e) { fail++; log('rss failed:', url, e.message); }
  }
  report.rss = { feeds: (cfg.rssFeeds || []).length, ok, fail };
  return out;
}

/** Wallapop public search API (best effort; the endpoint is undocumented and may change). */
export async function wallapopSource(cfg, report) {
  const out = [];
  let ok = 0, fail = 0;
  const L = cfg.location;
  for (const kw of ['pianista', 'violinista', 'músicos boda', 'pianista boda']) {
    try {
      const url = `https://api.wallapop.com/api/v3/general/search?keywords=${encodeURIComponent(kw)}&latitude=${L.lat}&longitude=${L.lon}&distance=${L.radiusKm * 1000}&order_by=newest&source=search_box`;
      const j = JSON.parse(await fetchText(url, { headers: { 'x-deviceos': '0', accept: 'application/json' } }));
      const items = j?.data?.section?.payload?.items || j?.search_objects || [];
      for (const i of items) {
        const slug = i.web_slug || i.slug;
        out.push({
          title: decodeEntities(i.title || ''), snippet: decodeEntities(i.description || ''),
          url: slug ? `https://es.wallapop.com/item/${slug}` : '', source: 'wallapop.com',
          lat: i.location?.latitude, lon: i.location?.longitude,
          date: i.modified_at || i.created_at ? new Date(i.modified_at || i.created_at).toISOString() : '',
        });
      }
      ok++;
    } catch (e) { fail++; if (fail <= 2) log('wallapop failed:', kw, e.message); }
    await sleep(800);
  }
  report.wallapop = { ok, fail };
  return out.filter((o) => o.url);
}

function hostOf(u) { try { return new URL(u).hostname.replace(/^www\./, ''); } catch { return ''; } }

export const SOURCES = [searchEngineSource, wallapopSource, rssSource];
