# Gig Finder 🎹🎻

Personal app that collects offers for piano/violin at weddings, baptisms, communions, birthdays, events and funerals within
100 km of Sagunto, and lets you contact each one in a tap (WhatsApp / email / call with a prefilled Spanish message).

## Run
```
cd gigfinder
npm start        # http://localhost:8080 — scrapes now and every hour
npm test
```
On your phone: open the URL → "Add to Home screen" (it's a PWA).

## Edit first
`config.json` → `me` (name, phone, bio, demo link). Put private overrides in `config.local.json` (git-ignored).

## Sources
| Source | How | Needs account? |
|---|---|---|
| Milanuncios, Vibbo, Wallapop, Facebook public posts, Bodas.net, InfoJobs, Indeed, Instagram… | Bing search per site (`src/sources.js`) | No |
| Wallapop | its search API, by your coordinates | No |
| Any Google Alerts / forum RSS | add URLs to `rssFeeds` | No |
| Facebook groups, Cronoshare leads, etc. | **"Search live" tab**: one-tap links to each platform's own filtered search, in your logged-in browser | Your own login, in your browser |

Not automated on purpose: logging into Facebook/Cronoshare with a bot violates their terms and risks banning your account.
Messages are never auto-sent; you press send.

## Hosting free & hourly
`.github/workflows/gigfinder.yml` re-scrapes hourly and commits `web/data/offers.json`. Serve `gigfinder/web` with any static host
(private-repo GitHub Pages needs a paid plan; Cloudflare Pages / Netlify free work). Push alerts: pick a secret topic name,
install the **ntfy** app, subscribe to it, and set it as `NTFY_TOPIC` (repo secret or `config.local.json`).
Note: some sites block datacenter IPs; running `npm start` on a home PC/Raspberry Pi is more reliable.

## Windows quick start
1. Install Node.js LTS from https://nodejs.org (one-time).
2. Download the repo (green **Code → Download ZIP**, branch `claude/festive-carson-ezxkqb`), unzip, open the `gigfinder` folder.
3. Double-click `start.bat`. Open http://localhost:8080. For your phone (same Wi-Fi): http://<PC-IP>:8080.

## Phone alerts (ntfy)
Install the **ntfy** app → Subscribe to topic shown in `config.json` (`ntfyTopic`). New offers (not musician ads) push to your phone.
Keep the topic name private: anyone who knows it can read the alerts.

## Phone access away from home
Same Wi-Fi: `http://<PC-IP>:8080`. Anywhere: install **Tailscale** (free) on PC and phone, then open `http://<PC-tailscale-name>:8080`.
