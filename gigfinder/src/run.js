import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { SOURCES } from './sources.js';
import { classify } from './classify.js';
import { quickLinks } from './links.js';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = resolve(ROOT, 'web/data/offers.json');

export async function loadConfig() {
  const cfg = JSON.parse(await readFile(resolve(ROOT, 'config.json'), 'utf8'));
  try { Object.assign(cfg, JSON.parse(await readFile(resolve(ROOT, 'config.local.json'), 'utf8'))); } catch {}
  if (process.env.NTFY_TOPIC) cfg.ntfyTopic = process.env.NTFY_TOPIC;
  return cfg;
}

export async function scrape() {
  const cfg = await loadConfig();
  let prev = { offers: [] };
  try { prev = JSON.parse(await readFile(OUT, 'utf8')); } catch {}
  const known = new Map(prev.offers.map((o) => [o.id, o]));
  const report = {};
  const now = new Date().toISOString();

  const raws = [];
  for (const src of SOURCES) {
    try { raws.push(...(await src(cfg, report))); } catch (e) { report[src.name] = { error: e.message }; }
  }

  const fresh = [];
  for (const raw of raws) {
    if (!raw.url || !raw.title) continue;
    const o = classify(raw, cfg);
    if (!o) continue;
    const old = known.get(o.id);
    if (old) { known.set(o.id, { ...old, ...o, firstSeen: old.firstSeen, lastSeen: now }); }
    else { const n = { ...o, firstSeen: now, lastSeen: now }; known.set(o.id, n); fresh.push(n); }
  }

  const cutoff = Date.now() - cfg.maxAgeDays * 864e5;
  const offers = [...known.values()]
    .filter((o) => new Date(o.firstSeen).getTime() > cutoff)
    .sort((a, b) => b.score - a.score || b.firstSeen.localeCompare(a.firstSeen));

  const data = { updated: now, report, location: cfg.location, me: cfg.me, links: quickLinks(cfg), offers };
  await mkdir(dirname(OUT), { recursive: true });
  await writeFile(OUT, JSON.stringify(data, null, 1));
  console.log(`done: ${raws.length} raw → ${offers.length} offers (${fresh.length} new)`, JSON.stringify(report));

  if (cfg.ntfyTopic && fresh.length) await notify(cfg, fresh.filter((o) => o.kind !== 'advert').slice(0, 5));
  return data;
}

async function notify(cfg, list) {
  for (const o of list) {
    try {
      await fetch(`https://ntfy.sh/${cfg.ntfyTopic}`, {
        method: 'POST', body: `${o.title}\n${o.town || o.source}`,
        headers: { Title: 'Nueva oferta de música', Click: o.url, Tags: 'musical_note' },
      });
    } catch (e) { console.log('ntfy failed', e.message); }
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) await scrape();
