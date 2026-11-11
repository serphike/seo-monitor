#!/usr/bin/env python3
"""Lightweight SEO monitor for low-RAM devices (Nokia 2 / Termux, Raspberry Pi).

Commands:
  python seo.py uptime        check key pages are up and fast (alerts on problems)
  python seo.py competitors   detect new/removed pages on competitor sitemaps
  python seo.py audit         on-page audit of your own site from its sitemap
  python seo.py brief         send the daily summary to Telegram
  python seo.py heartbeat     tiny "I'm alive" record (used by the watchdog)
"""
import json
import os
import re
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("SEO_DATA", os.path.join(BASE, "data"))
os.makedirs(DATA, exist_ok=True)
DB_PATH = os.path.join(DATA, "seo.db")
CONFIG_PATH = os.environ.get("SEO_CONFIG", os.path.join(DATA, "config.json"))
UA = "Mozilla/5.0 (Linux; Android 8.1) B2BSeoMonitor/1.0"
TIMEOUT = 25


# ---------------------------------------------------------------- helpers
def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def db():
    con = sqlite3.connect(DB_PATH)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS uptime(ts TEXT, url TEXT, status INT, ms INT, ok INT);
        CREATE TABLE IF NOT EXISTS comp_urls(domain TEXT, url TEXT, first_seen TEXT,
                                             last_seen TEXT, PRIMARY KEY(domain, url));
        CREATE TABLE IF NOT EXISTS comp_events(ts TEXT, domain TEXT, kind TEXT, url TEXT);
        CREATE TABLE IF NOT EXISTS audit(ts TEXT, url TEXT, status INT, issues TEXT);
        CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY, v TEXT);
        """
    )
    return con


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def kv_get(con, k, default=None):
    r = con.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
    return r[0] if r else default


def kv_set(con, k, v):
    con.execute("INSERT OR REPLACE INTO kv VALUES(?,?)", (k, str(v)))
    con.commit()


_session = requests.Session()
_session.headers["User-Agent"] = UA


def fetch(url, **kw):
    return _session.get(url, timeout=TIMEOUT, allow_redirects=True, **kw)


def telegram(cfg, text):
    """Send a Telegram message; prints instead if not configured."""
    token, chat = cfg.get("telegram_token"), cfg.get("telegram_chat_id")
    if not token or not chat:
        print("[telegram not configured]\n" + text)
        return False
    for chunk in [text[i:i + 3900] for i in range(0, len(text), 3900)] or [""]:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat, "text": chunk, "disable_web_page_preview": "true"},
                timeout=TIMEOUT,
            )
        except requests.RequestException as e:
            print("telegram error:", e)
            return False
    return True


def domain_of(url):
    return urlparse(url).netloc.lower().removeprefix("www.")


# ---------------------------------------------------------------- sitemaps
SITEMAP_GUESSES = ["/sitemap_index.xml", "/sitemap.xml", "/wp-sitemap.xml", "/page-sitemap.xml"]


def _sitemaps_from_robots(root):
    try:
        r = fetch(urljoin(root, "/robots.txt"))
        if r.ok:
            return re.findall(r"(?im)^\s*sitemap:\s*(\S+)", r.text)
    except requests.RequestException:
        pass
    return []


def sitemap_urls(root, limit=5000):
    """Return the set of page URLs listed in a site's sitemaps (follows indexes)."""
    queue = _sitemaps_from_robots(root) or [urljoin(root, g) for g in SITEMAP_GUESSES]
    seen, pages = set(), set()
    while queue and len(pages) < limit and len(seen) < 60:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        try:
            r = fetch(sm)
            if not r.ok or b"<" not in r.content[:200]:
                continue
            tree = ET.fromstring(r.content)
        except (requests.RequestException, ET.ParseError):
            continue
        tag = tree.tag.lower()
        locs = [e.text.strip() for e in tree.iter() if e.tag.lower().endswith("loc") and e.text]
        if tag.endswith("sitemapindex"):
            queue.extend(locs)
        else:
            pages.update(u for u in locs if not re.search(r"\.(jpe?g|png|gif|webp|pdf|svg)$", u, re.I))
        if pages and not tag.endswith("sitemapindex") and sm.endswith(tuple(SITEMAP_GUESSES)):
            # a plain sitemap guess worked; no need to try the other guesses
            queue = [q for q in queue if not q.endswith(tuple(SITEMAP_GUESSES))]
    return pages


# ---------------------------------------------------------------- uptime
def cmd_uptime(cfg):
    con = db()
    problems = []
    for path in cfg.get("key_pages", ["/"]):
        url = urljoin(cfg["site"], path)
        t0 = time.time()
        try:
            r = fetch(url)
            ms, status = int((time.time() - t0) * 1000), r.status_code
        except requests.RequestException as e:
            ms, status = int((time.time() - t0) * 1000), 0
            print("error", url, e)
        ok = int(status == 200 and ms < cfg.get("slow_ms", 4000))
        con.execute("INSERT INTO uptime VALUES(?,?,?,?,?)", (now(), url, status, ms, ok))
        if not ok:
            problems.append(f"{url} → status {status or 'DOWN'}, {ms} ms")
    con.commit()
    # alert only on a state change, so you are not spammed every 15 minutes
    was_down = kv_get(con, "site_down") == "1"
    if problems and not was_down:
        telegram(cfg, "🔴 Site problem\n" + "\n".join(problems))
        kv_set(con, "site_down", 1)
    elif not problems and was_down:
        telegram(cfg, "🟢 Site is back to normal: " + cfg["site"])
        kv_set(con, "site_down", 0)
    print("uptime:", "problems" if problems else "ok")


# ---------------------------------------------------------------- competitors
def cmd_competitors(cfg):
    con = db()
    ts = now()
    lines = []
    for comp in cfg.get("competitors", []):
        dom = domain_of(comp)
        urls = sitemap_urls(comp)
        if not urls:
            print("no sitemap found for", dom)
            continue
        known = {r[0] for r in con.execute("SELECT url FROM comp_urls WHERE domain=?", (dom,))}
        first_run = not known
        new = sorted(urls - known)
        gone = sorted(known - urls)
        con.executemany(
            "INSERT INTO comp_urls VALUES(?,?,?,?) ON CONFLICT(domain,url) DO UPDATE SET last_seen=excluded.last_seen",
            [(dom, u, ts, ts) for u in urls],
        )
        if gone:
            con.executemany("DELETE FROM comp_urls WHERE domain=? AND url=?", [(dom, u) for u in gone])
        if first_run:
            lines.append(f"📥 {dom}: now tracking {len(urls)} pages")
            continue
        con.executemany("INSERT INTO comp_events VALUES(?,?,?,?)",
                        [(ts, dom, "new", u) for u in new] + [(ts, dom, "removed", u) for u in gone])
        if new:
            lines.append(f"🆕 {dom} published {len(new)} new page(s):\n" + "\n".join("  • " + u for u in new[:10]))
            if len(new) > 10:
                lines.append(f"  …and {len(new) - 10} more")
        if gone:
            lines.append(f"🗑 {dom} removed {len(gone)} page(s)")
    con.commit()
    if lines:
        telegram(cfg, "🕵️ Competitor watch\n\n" + "\n\n".join(lines))
    print("competitors: done,", len(lines), "updates")


# ---------------------------------------------------------------- audit
def audit_page(url, html, status):
    issues = []
    if status != 200:
        return [f"status {status}"]
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    desc_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    desc = (desc_tag.get("content") or "").strip() if desc_tag else ""
    h1s = soup.find_all("h1")
    canon = soup.find("link", rel=lambda v: v and "canonical" in v)
    robots = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})
    if not title:
        issues.append("missing title")
    elif len(title) > 65:
        issues.append(f"title too long ({len(title)})")
    elif len(title) < 25:
        issues.append(f"title too short ({len(title)})")
    if not desc:
        issues.append("missing meta description")
    elif len(desc) > 160:
        issues.append(f"meta description too long ({len(desc)})")
    if len(h1s) == 0:
        issues.append("no H1")
    elif len(h1s) > 1:
        issues.append(f"{len(h1s)} H1 tags")
    if not canon:
        issues.append("no canonical")
    elif canon.get("href") and canon["href"].rstrip("/") != url.rstrip("/"):
        issues.append("canonical points elsewhere")
    if robots and "noindex" in (robots.get("content") or "").lower():
        issues.append("NOINDEX")
    imgs = soup.find_all("img")
    no_alt = sum(1 for i in imgs if not (i.get("alt") or "").strip())
    if no_alt:
        issues.append(f"{no_alt} image(s) without alt")
    words = len(soup.get_text(" ", strip=True).split())
    if words < 300:
        issues.append(f"thin content ({words} words)")
    return issues


def cmd_audit(cfg):
    con = db()
    ts = now()
    urls = sorted(sitemap_urls(cfg["site"]))[: cfg.get("audit_max_pages", 150)]
    if not urls:
        urls = [cfg["site"]]
    titles, results = {}, []
    for u in urls:
        try:
            r = fetch(u)
            status, html = r.status_code, r.text
        except requests.RequestException:
            status, html = 0, ""
        issues = audit_page(u, html, status)
        if status == 200:
            t = BeautifulSoup(html, "html.parser").title
            if t and t.string:
                titles.setdefault(t.string.strip(), []).append(u)
        results.append((u, status, issues))
        time.sleep(0.5)  # be gentle with your own server
    for t, us in titles.items():
        if len(us) > 1:
            for u, _, iss in results:
                if u in us:
                    iss.append("duplicate title")
    con.executemany("INSERT INTO audit VALUES(?,?,?,?)",
                    [(ts, u, s, json.dumps(i)) for u, s, i in results])
    con.commit()
    counts = {}
    for _, _, iss in results:
        for i in iss:
            key = re.sub(r"\s*\(.*?\)", "", i)
            key = re.sub(r"^\d+ H1 tags$", "multiple H1 tags", key)
            key = re.sub(r"^\d+ ", "", key)
            counts[key] = counts.get(key, 0) + 1
    bad = [r for r in results if r[2]]
    msg = [f"🔎 Weekly audit: {len(results)} pages, {len(bad)} with issues"]
    for k, v in sorted(counts.items(), key=lambda x: -x[1])[:10]:
        msg.append(f"  • {k}: {v} page(s)")
    critical = [r for r in results if r[1] != 200 or "NOINDEX" in r[2]]
    if critical:
        msg.append("\n⚠️ Fix first:")
        msg += [f"  • {u} — {', '.join(i)}" for u, _, i in critical[:10]]
    telegram(cfg, "\n".join(msg))
    # keep a CSV so it can be uploaded to Google Drive later
    with open(os.path.join(DATA, "audit_latest.csv"), "w") as f:
        f.write("url,status,issues\n")
        for u, s, i in results:
            f.write(f'"{u}",{s},"{"; ".join(i)}"\n')
    print("audit: done,", len(results), "pages")


# ---------------------------------------------------------------- brief
def cmd_brief(cfg):
    con = db()
    since = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    rows = con.execute("SELECT ok, ms FROM uptime WHERE ts>=?", (since,)).fetchall()
    checks = len(rows)
    up = sum(r[0] for r in rows)
    avg = int(sum(r[1] for r in rows) / checks) if checks else 0
    ev = con.execute(
        "SELECT domain, COUNT(*) FROM comp_events WHERE ts>=? AND kind='new' GROUP BY domain", (since,)
    ).fetchall()
    last_audit = con.execute("SELECT MAX(ts) FROM audit").fetchone()[0]
    lines = [f"☀️ Daily brief — {datetime.now():%d %b %Y}", ""]
    if checks:
        lines.append(f"Uptime: {up}/{checks} checks OK ({100 * up // checks}%), avg {avg} ms")
    else:
        lines.append("Uptime: no checks in the last 24h ⚠️")
    if ev:
        lines.append("Competitor new pages (24h): " + ", ".join(f"{d} +{n}" for d, n in ev))
    else:
        lines.append("Competitor new pages (24h): none")
    if last_audit:
        n_bad = con.execute("SELECT COUNT(*) FROM audit WHERE ts=? AND issues!='[]'", (last_audit,)).fetchone()[0]
        lines.append(f"Last audit {last_audit[:10]}: {n_bad} page(s) with issues")
    telegram(cfg, "\n".join(lines))
    print("brief: sent")


def cmd_heartbeat(cfg):
    con = db()
    kv_set(con, "heartbeat", now())
    print("heartbeat")


COMMANDS = {
    "uptime": cmd_uptime,
    "competitors": cmd_competitors,
    "audit": cmd_audit,
    "brief": cmd_brief,
    "heartbeat": cmd_heartbeat,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]](load_config())
