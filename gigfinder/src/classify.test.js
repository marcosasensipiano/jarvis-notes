import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { classify } from './classify.js';
import { parseFeed } from './lib.js';

const cfg = JSON.parse(readFileSync(new URL('../config.json', import.meta.url)));
const mk = (title, snippet = '', url = 'https://www.milanuncios.com/x/1.htm') => ({ title, snippet, url, source: 'milanuncios.com' });

test('demand offer near Sagunto scores high with contact', () => {
  const o = classify(mk('Se busca pianista para boda en Puerto de Sagunto', 'Llamar al 612 345 678 o a boda@ejemplo.es'), cfg);
  assert.equal(o.kind, 'demand');
  assert.equal(o.town, 'Puerto de Sagunto');
  assert.equal(o.contact.phone, '612345678');
  assert.equal(o.contact.whatsapp, 'https://wa.me/34612345678');
  assert.equal(o.contact.email, 'boda@ejemplo.es');
  assert.ok(o.score >= 8);
});
test('musician advert is flagged', () => {
  assert.equal(classify(mk('Ofrezco violinista para bodas y eventos', 'disponible en Valencia'), cfg).kind, 'advert');
});
test('outside radius is dropped', () => {
  assert.equal(classify(mk('Se busca pianista boda Torrevieja'), cfg), null);
});
test('irrelevant is dropped', () => {
  assert.equal(classify(mk('Vendo coche', 'barato'), cfg), null);
});
test('rss parser', () => {
  const xml = '<rss><channel><item><title><![CDATA[A &amp; B]]></title><link>https://x.es/a</link><description>d</description></item></channel></rss>';
  assert.deepEqual(parseFeed(xml)[0].url, 'https://x.es/a');
});
