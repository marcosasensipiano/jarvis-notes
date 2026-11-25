const $ = (s) => document.querySelector(s);
const LS = {
  get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
};
let data = { offers: [], links: [], me: {} };
let state = LS.get('state', {});            // id -> 'contacted' | 'dismissed'
let tpl = LS.get('tpl', '');
let tab = 'offers';
const f = { q: '', onlyNew: false, noAds: true, hideDone: false };
const lastVisit = new Date(LS.get("lastVisit", 0));
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const DEFAULT_TPL = `Hola, buenos días. Vi su anuncio "{title}" y me gustaría ofrecerle mis servicios musicales. Soy {name}, {bio}. {demo}Podría indicarme fecha, lugar y tipo de evento para enviarle un presupuesto sin compromiso. ¡Muchas gracias!`;

function draft(o) {
  const me = data.me || {};
  return (tpl || DEFAULT_TPL)
    .replaceAll('{title}', o.title).replaceAll('{name}', me.name || '').replaceAll('{bio}', me.bio || '')
    .replaceAll('{demo}', me.demoLink ? `Aquí puede escucharme: ${me.demoLink}. ` : '').replaceAll('{phone}', me.phone || '');
}

async function load() {
  try {
    data = await (await fetch('data/offers.json?' + Date.now())).json();
    const u = new Date(data.updated);
    const r = data.report || {};
    const parts = Object.entries(r).map(([k, v]) => v.error ? `${k}: error` : `${k} ${v.ok ?? ''}${v.queries ? '/' + v.queries : v.feeds != null ? '/' + v.feeds : ''}`);
    $('#status').textContent = `Updated ${u.toLocaleString()} · ${data.offers.length} offers · ${parts.join(' · ')}`;
    $('#where').textContent = `· ${data.location?.name} ${data.location?.radiusKm} km`;
  } catch { $('#status').textContent = 'No data yet — run "npm run scrape" or wait for the next hourly update.'; }
  render();
}

function render() {
  $('#fbar').style.display = tab === 'offers' ? '' : 'none';
  for (const t of ['offers', 'links', 'set']) $('#t-' + t).classList.toggle('on', tab === t);
  if (tab === 'links') return renderLinks();
  if (tab === 'set') return renderSettings();
  const q = f.q.toLowerCase();
  const list = data.offers.filter((o) =>
    (!q || (o.title + o.snippet + o.town + o.source).toLowerCase().includes(q)) &&
    (!f.onlyNew || new Date(o.firstSeen) > lastVisit) &&
    (!f.noAds || o.kind !== 'advert') &&
    (!f.hideDone || state[o.id] !== 'dismissed'));
  $('#main').innerHTML = list.length ? list.map(card).join('') : '<p class="mut">Nothing yet. Use "Search live" for one-tap searches on every platform.</p>';
}

function card(o) {
  const isNew = new Date(o.firstSeen) > lastVisit;
  const c = o.contact || {};
  const msg = encodeURIComponent(draft(o));
  const st = state[o.id];
  return `<div class="card ${st ? 'done' : ''}" data-id="${o.id}">
    <div>${isNew ? '<span class="tag new">NEW</span>' : ''}${o.kind === 'demand' ? '<span class="tag demand">looking for musician</span>' : ''}${o.kind === 'advert' ? '<span class="tag">musician ad</span>' : ''}
      <span class="tag">${esc(o.source)}</span>${o.town ? `<span class="tag">📍 ${esc(o.town)}${o.distKm != null ? ' · ' + o.distKm + ' km' : ''}</span>` : ''}${o.events.slice(0, 3).map((e) => `<span class="tag">${esc(e)}</span>`).join('')}${st ? `<span class="tag">${st}</span>` : ''}</div>
    <h3>${esc(o.title)}</h3>
    <div class="mut">${esc(o.snippet)}</div>
    <small class="mut">found ${new Date(o.firstSeen).toLocaleString()}${o.postedAt ? ' · posted ' + new Date(o.postedAt).toLocaleDateString() : ''}</small>
    <div class="btns">
      <a href="${esc(o.url)}" target="_blank" rel="noopener">Open offer</a>
      ${c.whatsapp ? `<a href="${c.whatsapp}?text=${msg}" target="_blank" rel="noopener">WhatsApp</a>` : ''}
      ${c.email ? `<a href="mailto:${esc(c.email)}?subject=${encodeURIComponent('Música en directo: ' + o.title.slice(0, 60))}&body=${msg}">Email</a>` : ''}
      ${c.phone ? `<a href="tel:+34${c.phone}">Call</a>` : ''}
      <button class="alt" data-act="copy">Copy message</button>
      <button class="alt" data-act="contacted">✓ Contacted</button>
      <button class="alt" data-act="dismissed">✕</button>
    </div></div>`;
}

function renderLinks() {
  const groups = {};
  for (const l of data.links || []) (groups[l.group] ||= []).push(l);
  $('#main').innerHTML = '<p class="mut">Live searches on each platform, already filtered by your area. Open them in your logged-in browser/app (Facebook, Wallapop…).</p>' +
    Object.entries(groups).map(([g, ls]) => `<div class="grp">${esc(g)}</div><div class="links">${ls.map((l) => `<a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label)}</a>`).join('')}</div>`).join('');
}

function renderSettings() {
  $('#main').innerHTML = `<p class="mut">Your reply template (Spanish). Placeholders: {title} {name} {bio} {demo} {phone}. Name/bio/demo come from config.json.</p>
  <textarea id="tpl">${esc(tpl || DEFAULT_TPL)}</textarea>
  <div class="btns"><button id="save">Save</button><button class="alt" id="reset">Reset</button></div>`;
  $('#save').onclick = () => { tpl = $('#tpl').value; LS.set('tpl', tpl); alert('Saved'); };
  $('#reset').onclick = () => { tpl = ''; LS.set('tpl', ''); renderSettings(); };
}

$('#main').addEventListener('click', async (e) => {
  const b = e.target.closest('button[data-act]'); if (!b) return;
  const id = b.closest('.card').dataset.id, o = data.offers.find((x) => x.id === id);
  if (b.dataset.act === 'copy') { try { await navigator.clipboard.writeText(draft(o)); b.textContent = 'Copied ✓'; } catch { prompt('Copy:', draft(o)); } return; }
  state[id] = state[id] === b.dataset.act ? undefined : b.dataset.act; LS.set('state', state); render();
});
$('#q').oninput = (e) => { f.q = e.target.value; render(); };
const tog = (id, k) => { $(id).onclick = () => { f[k] = !f[k]; $(id).classList.toggle('on', f[k]); render(); }; };
tog('#f-new', 'onlyNew'); tog('#f-demand', 'noAds'); tog('#f-hide', 'hideDone');
$('#f-ref').onclick = async () => { try { await fetch('refresh', { method: 'POST' }); $('#status').textContent = 'Refreshing… reload in ~1 min'; } catch {} setTimeout(load, 500); };
for (const t of ['offers', 'links', 'set']) $('#t-' + t).onclick = () => { tab = t; render(); };

load();
LS.set('lastVisit', Date.now());
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
