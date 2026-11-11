#!/data/data/com.termux/files/usr/bin/bash
# One-shot installer for Termux (Nokia 2). Safe to run again.
# Usage: bash install.sh <git-repo-url>
set -e
REPO_URL="${1:-$REPO_URL}"
APP="$HOME/seo-monitor"

echo "== 1/6 Installing packages (can take a while on an old phone) =="
pkg update -y >/dev/null || true
pkg install -y python git cronie termux-api >/dev/null
pip install -q requests beautifulsoup4

echo "== 2/6 Getting the code =="
if [ -d "$APP/.git" ]; then
  git -C "$APP" pull --ff-only
elif [ -n "$REPO_URL" ]; then
  git clone "$REPO_URL" "$APP"
else
  echo "No repo URL given. Usage: bash install.sh <git-repo-url>"; exit 1
fi
mkdir -p "$APP/data"
cd "$APP"

echo "== 3/6 Telegram setup =="
if [ ! -f data/config.json ]; then
  cp config.example.json data/config.json
fi
TOKEN=$(python -c "import json;print(json.load(open('data/config.json'))['telegram_token'])")
if [ -z "$TOKEN" ]; then
  echo "Paste your Telegram bot token from @BotFather, then press Enter:"
  read -r TOKEN
fi
echo "Now open your bot in Telegram and send it any message (e.g. hi). Press Enter here when done."
read -r _
TOKEN=$(echo "$TOKEN" | tr -d '[:space:]')
CHAT=$(python - "$TOKEN" <<'PY'
import sys, time, requests
for attempt in range(3):
    try:
        r = requests.get(f"https://api.telegram.org/bot{sys.argv[1]}/getUpdates", timeout=30)
        break
    except requests.RequestException as e:
        print(f"  network problem talking to Telegram (try {attempt+1}/3): {type(e).__name__}", file=sys.stderr)
        time.sleep(5)
else:
    print("  Can't reach api.telegram.org. Check the phone's internet (open any website), then run the installer again.", file=sys.stderr)
    sys.exit(0)
if r.status_code == 401 or r.status_code == 404:
    print("  Telegram says this token is wrong. Copy it again from @BotFather.", file=sys.stderr)
    sys.exit(0)
ids = [u["message"]["chat"]["id"] for u in r.json().get("result", []) if "message" in u]
print(ids[-1] if ids else "")
PY
)
if [ -z "$CHAT" ]; then
  echo "Couldn't find your chat. Check the token, message the bot, and run this installer again."; exit 1
fi
python - "$TOKEN" "$CHAT" <<'PY'
import json, sys
p = "data/config.json"
c = json.load(open(p)); c["telegram_token"] = sys.argv[1]; c["telegram_chat_id"] = sys.argv[2]
json.dump(c, open(p, "w"), indent=2)
PY
chmod 600 data/config.json
echo "Telegram linked (chat $CHAT)."

echo "== 4/6 Scheduling jobs =="
HOUR=$(python -c "import json;print(json.load(open('data/config.json')).get('brief_hour',9))")
PY="$(command -v python)"
crontab - <<CRON
*/15 * * * * cd $APP && $PY seo.py uptime >> data/log.txt 2>&1
*/30 * * * * cd $APP && $PY seo.py heartbeat >/dev/null 2>&1
0 7 * * *    cd $APP && $PY seo.py competitors >> data/log.txt 2>&1
0 $HOUR * * * cd $APP && $PY seo.py brief >> data/log.txt 2>&1
0 3 * * 0    cd $APP && $PY seo.py audit >> data/log.txt 2>&1
30 2 * * *   cd $APP && git pull --ff-only >> data/log.txt 2>&1 && pkill -f bot.py; true
0 4 * * 1    tail -n 2000 $APP/data/log.txt > $APP/data/log.tmp && mv $APP/data/log.tmp $APP/data/log.txt
CRON

echo "== 5/6 Auto-start after reboot (Termux:Boot) =="
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/start-seo.sh" <<BOOT
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
crond
cd $APP && nohup sh run-bot.sh >> data/bot.log 2>&1 &
BOOT
chmod +x "$HOME/.termux/boot/start-seo.sh" run-bot.sh

echo "== 6/6 Starting now =="
pkill -f run-bot.sh 2>/dev/null || true
pkill -f bot.py 2>/dev/null || true
sh "$HOME/.termux/boot/start-seo.sh"
python seo.py uptime
python seo.py competitors
python - <<'PY'
import seo
seo.telegram(seo.load_config(), "✅ SEO monitor installed on your phone.\nSend /help to see commands.")
PY
echo
echo "DONE. Check Telegram. You can close Termux (don't swipe it away from recent apps)."
