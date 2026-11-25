// One-tap search links for platforms that can't (or shouldn't) be scraped automatically — they open the
// platform's own live search, filtered for the area, in your logged-in browser/app.
export function quickLinks(cfg) {
  const L = cfg.location;
  const e = encodeURIComponent;
  const terms = ['pianista boda', 'violinista boda', 'músicos boda', 'pianista evento', 'violinista funeral', 'pianista bautizo'];
  const links = [];
  for (const t of terms) {
    links.push(
      { group: 'Milanuncios', label: t, url: `https://www.milanuncios.com/anuncios-en-valencia/?s=${e(t)}&orden=date` },
      { group: 'Wallapop', label: t, url: `https://es.wallapop.com/app/search?keywords=${e(t)}&latitude=${L.lat}&longitude=${L.lon}&distance=${L.radiusKm * 1000}&order_by=newest` },
      { group: 'Vibbo', label: t, url: `https://www.vibbo.com/anuncios-valencia/?q=${e(t)}` },
      { group: 'Facebook (posts)', label: t, url: `https://www.facebook.com/search/posts/?q=${e(t + ' ' + L.name)}` },
      { group: 'Facebook (groups)', label: t, url: `https://www.facebook.com/search/groups/?q=${e('músicos ' + t.split(' ').pop() + ' Valencia')}` },
      { group: 'Google (last week)', label: t, url: `https://www.google.com/search?q=${e('se busca ' + t + ' ' + L.name)}&tbs=qdr:w` },
      { group: 'Instagram', label: t, url: `https://www.instagram.com/explore/search/keyword/?q=${e(t)}` },
    );
  }
  links.push(
    { group: 'Marketplaces', label: 'Cronoshare – Música (leads)', url: 'https://www.cronoshare.com/' },
    { group: 'Marketplaces', label: 'Bodas.net – proveedores música', url: 'https://www.bodas.net/musica-boda/valencia' },
    { group: 'Marketplaces', label: 'Superprof (clases piano/violín)', url: 'https://www.superprof.es/' },
    { group: 'Marketplaces', label: 'InfoJobs – músico', url: `https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=${e('músico pianista violinista')}&provinceIds=47` },
    { group: 'Marketplaces', label: 'Indeed – pianista', url: `https://es.indeed.com/jobs?q=${e('pianista violinista')}&l=${e(L.name)}&radius=${L.radiusKm}` },
    { group: 'Marketplaces', label: 'GigSalad', url: 'https://www.gigsalad.com/' },
    { group: 'Marketplaces', label: 'SoundBetter', url: 'https://soundbetter.com/' },
  );
  return links;
}
