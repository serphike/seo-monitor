# myhq.in audit: evidence (25 Nov 2026)

Every claim in the audit doc can be checked against the URLs and data in this folder.

| File | What it backs |
| --- | --- |
| [duplicate-titles.md](duplicate-titles.md) | 493 URLs sharing a title, grouped by title |
| [missing-h1.md](missing-h1.md) | 557 URLs without an `<h1>` |
| [duplicate-meta-descriptions.md](duplicate-meta-descriptions.md) | 1,281 URLs sharing a meta description, grouped |
| [slow-pages.md](slow-pages.md) | 112 URLs that took over 3 s to load in the crawl, slowest first |
| [raw/](raw/) | Raw JSON exports from the crawl tool for the three lists above |

**Source:** Ubersuggest site audit, 10,000 pages crawled from a US IP (crawler gateway 68.183.157.22) on 25 Nov 2026. Health score 76. 9,525 pages returned 200, 455 redirected, 20 were broken and 0 were blocked.

Results reflect the site on the crawl date. A page fixed since then will no longer show the issue.

## URLs returning 4xx (19)

All returned HTTP 404 in the crawl.

| URL |
| --- |
| https://myhq.in/coworking-space |
| https://myhq.in/office-space |
| https://myhq.in/meeting-rooms |
| https://myhq.in/day-pass |
| https://myhq.in/event-spaces |
| https://myhq.in/commercial-office-space |
| https://myhq.in/bangalore/coworking-space/banerghatta-road |
| https://myhq.in/gurugram/coworking-space/m-g-road-gurgaon |
| https://myhq.in/gurugram/coworking-space/udyog-vihar-phase-iv |
| https://myhq.in/gurugram/meeting-room/m-g-road-gurgaon |
| https://myhq.in/flexi/coworking-space/quickstart-coworking--sita-shelters-begumpet |
| https://myhq.in/blog/virtual-office/virtual-office-in-india-for-gst-registration |
| https://myhq.in/blog/virtual-office/virtual-office-in-kochi-complete-guide |
| https://myhq.in/flexi/?utm_source=digest.myhq.in&utm_medium=blog&utm_campaign=Flexi |
| https://myhq.in/bangalore/day-pass/bangalore%3Ffilters%3D%7B%22FLEXI_SPACE_TYPE%22:%22WORKCAFE%22%7D |
| https://myhq.in/gurugram/day-pass/gurugram%3Ffilters%3D%7B%22FLEXI_SPACE_TYPE%22:%22WORKCAFE%22%7D |
| https://myhq.in/new-delhi/day-pass/new-delhi%3Ffilters%3D%7B%22FLEXI_SPACE_TYPE%22:%22WORKCAFE%22%7D |
| https://myhq.in/noida/day-pass/noida%3Ffilters%3D%7B%22FLEXI_SPACE_TYPE%22:%22WORKCAFE%22%7D |
| https://myhq.in/cdn-cgi/l/email-protection |

The last URL is a Cloudflare email-obfuscation path and can be ignored.

## Low word count (20)

| URL | Words |
| --- | --- |
| https://digest.myhq.in/blog/ | 9 |
| https://myhq.in/find-your-virtual-office-with-ai?source=LISTING_PAGE&position=HEADER | 87 |
| https://myhq.in/ | 111 |
| https://myhq.in/dedicated/coworking-space-in- | 111 |
| https://myhq.in/dedicated/coworking-space-in-?utm_source=blogwebsite&utm_medium=myhq.in/blog&utm_channel=organic&utm_campaign=dedicated | 111 |
| https://myhq.in/event-space | 111 |
| https://myhq.in/flexi/coworking-space-in- | 111 |
| https://myhq.in/managed-office | 111 |
| https://myhq.in/managed-office?utm_source=blogwebsite&utm_medium=myhq.in/blog&utm_channel=organic&utm_campaign=dedicated | 111 |
| https://myhq.in/meeting-room | 111 |
| https://myhq.in/meeting-room?utm_source=digest.myhq.in&utm_medium=blog&utm_campaign=footer_links_virtual&utm_channel=organic | 111 |
| https://myhq.in/office-space-for-rent | 111 |
| https://myhq.in/list-space | 114 |
| https://myhq.in/meeting-room/incuspaze-ub-city-ashoknagar | 125 |
| https://myhq.in/shortlisted-workspaces | 129 |
| https://myhq.in/dedicated/coworking-space/awfis-prestige-zackria-metropolitan | 137 |
| https://myhq.in/dedicated/coworking-space/pinnacle-space-connaughtplace | 137 |
| https://myhq.in/dedicated/coworking-space/startup-business-center-banjarahills | 137 |
| https://myhq.in/dedicated/coworking-space/the-work-culture-indrapuri | 137 |
| https://myhq.in/blog | 178 |

## robots.txt (fetched 25 Nov 2026)

https://myhq.in/robots.txt

```
User-agent: *
Disallow: /meeting-room/payment
Disallow: /flexi/desk/book
Disallow: /flexi/premium-desk/book
Disallow: /flexi/cabin/book
Disallow: /virtual-office/payments
Disallow: /credit-campaign
Disallow: /empty

Sitemap: https://myhq.in/sitemap.xml
```

## Cloudflare challenge (our test client, 25 Nov 2026)

A request with a Chrome user-agent from our cloud test environment got these responses:

```
GET https://myhq.in/              -> HTTP/2 403, server: cloudflare, cf-mitigated: challenge, <title>Just a moment...</title>, <meta name="robots" content="noindex,nofollow">
GET https://myhq.in/sitemap.xml   -> HTTP/2 403 (challenge)
GET https://myhq.in/noida/dedicated/coworking-space-in-noida -> 403 (challenge)
GET https://myhq.in/blog/cin-number -> 403 (challenge)
GET https://myhq.in/robots.txt    -> HTTP/2 200, server: cloudflare, cf-cache-status: HIT
```

Over the same period, the Ubersuggest crawler fetched 10,000 pages with 0 blocked. So Cloudflare challenges some clients or IP ranges, not all automated traffic. To reproduce, run `curl -sI https://myhq.in/` from a cloud server and look for `cf-mitigated: challenge`.
