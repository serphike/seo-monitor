#!/usr/bin/env python3
"""Telegram command bot. Only answers the chat_id in config.json.

/status       uptime + last checks
/brief        send the daily brief now
/audit        run the site audit now (takes a few minutes)
/competitors  check competitor sitemaps now
/update       pull the latest code from GitHub
/help         this list
"""
import os
import subprocess
import sys
import time

import requests

import seo

HELP = __doc__.split("\n", 2)[2]


def run(*args):
    p = subprocess.run([sys.executable, os.path.join(seo.BASE, "seo.py"), *args],
                       capture_output=True, text=True, timeout=1800)
    return (p.stdout + p.stderr).strip()[-1500:]


def status_text():
    con = seo.db()
    rows = con.execute("SELECT ts, url, status, ms FROM uptime ORDER BY ts DESC LIMIT 5").fetchall()
    hb = seo.kv_get(con, "heartbeat", "never")
    out = [f"📱 Phone alive. Last heartbeat: {hb}", "Last checks:"]
    out += [f"  {ts[11:16]} {status or 'DOWN'} {ms}ms {url}" for ts, url, status, ms in rows] or ["  none yet"]
    return "\n".join(out)


def main():
    cfg = seo.load_config()
    token, chat = cfg["telegram_token"], str(cfg["telegram_chat_id"])
    api = f"https://api.telegram.org/bot{token}"
    offset = None
    print("bot running")
    while True:
        try:
            r = requests.get(f"{api}/getUpdates", params={"timeout": 50, "offset": offset}, timeout=60)
            updates = r.json().get("result", [])
        except Exception as e:  # network drops are normal on a phone
            print("poll error:", e)
            time.sleep(15)
            continue
        for u in updates:
            offset = u["update_id"] + 1
            msg = u.get("message") or {}
            if str(msg.get("chat", {}).get("id")) != chat:
                continue  # ignore strangers
            cmd = (msg.get("text") or "").split()[0].split("@")[0].lower() if msg.get("text") else ""
            if cmd == "/status":
                reply = status_text()
            elif cmd == "/brief":
                run("brief")  # seo.py sends the message itself
                reply = None
            elif cmd == "/audit":
                seo.telegram(cfg, "⏳ Audit started, results in a few minutes…")
                run("audit")
                reply = None
            elif cmd == "/competitors":
                seo.telegram(cfg, "⏳ Checking competitors…")
                out = run("competitors")
                reply = "No competitor changes." if out.endswith(" 0 updates") else None
            elif cmd == "/update":
                p = subprocess.run(["git", "-C", seo.BASE, "pull", "--ff-only"], capture_output=True, text=True)
                reply = "🔄 " + (p.stdout + p.stderr).strip()[-1000:] + "\nRestarting bot…"
                seo.telegram(cfg, reply)
                os.execv(sys.executable, [sys.executable] + sys.argv)
            elif cmd in ("/help", "/start"):
                reply = "Commands:\n" + HELP
            else:
                reply = None
            if reply:
                seo.telegram(cfg, reply)


if __name__ == "__main__":
    main()
