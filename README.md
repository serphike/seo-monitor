# B2B SEO Monitor (phone / Raspberry Pi)

A small SEO monitoring system for b2b-seoservices.com. It runs on a Nokia 2 in Termux, or on a Raspberry Pi.

| Job | When | What you get on Telegram |
|---|---|---|
| Uptime + speed | every 15 min | alert when the site goes down or slow, and when it recovers |
| Competitor watch | daily 07:00 | new or removed pages on competitor sitemaps |
| Daily brief | daily 09:00 | uptime %, avg speed, competitor activity, audit status |
| Site audit | Sunday 03:00 | title, meta, H1, canonical, noindex, alt, thin content, duplicates, 404s |
| Self-update | daily 02:30 | pulls new code from this repo |

Bot commands: `/status /brief /audit /competitors /update /help`

## Install (Termux)
```
pkg install -y git && git clone <REPO_URL> ~/seo-monitor && bash ~/seo-monitor/install.sh
```
Settings live in `data/config.json` (competitors, key pages, brief hour). This file is not committed.
