#!/bin/bash
# Start the bot in the background
python3 src/bot.py &
# Start the API server in the foreground
exec python3 src/main.py
