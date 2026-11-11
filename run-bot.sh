#!/data/data/com.termux/files/usr/bin/sh
# Keeps the Telegram bot running; restarts it if it crashes or after a nightly update.
cd "$(dirname "$0")"
while true; do
  python bot.py
  sleep 10
done
