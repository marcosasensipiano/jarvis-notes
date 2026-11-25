// Local server: serves the PWA and re-scrapes every hour. `npm start` → http://localhost:8080
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { resolve, dirname, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { scrape } from './run.js';

const WEB = resolve(dirname(fileURLToPath(import.meta.url)), '../web');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json' };
let running = false;
async function refresh() { if (running) return; running = true; try { await scrape(); } catch (e) { console.error(e); } finally { running = false; } }

createServer(async (req, res) => {
  const p = new URL(req.url, 'http://x').pathname;
  if (p === '/refresh' && req.method === 'POST') { refresh(); res.writeHead(202).end('started'); return; }
  const file = resolve(WEB, '.' + (p === '/' ? '/index.html' : p));
  if (!file.startsWith(WEB)) { res.writeHead(403).end(); return; }
  try { res.writeHead(200, { 'content-type': TYPES[extname(file)] || 'text/plain' }).end(await readFile(file)); }
  catch { res.writeHead(404).end('not found'); }
}).listen(process.env.PORT || 8080, '0.0.0.0', () => console.log('http://localhost:' + (process.env.PORT || 8080)));

refresh();
setInterval(refresh, 60 * 60 * 1000);
