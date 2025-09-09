# Discord Event Bot

A lightweight Discord bot for managing week-long events with progress tracking and leaderboards.

## Setup

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Add your Discord bot token to `.env`:
     ```
     DISCORD_TOKEN=your_actual_bot_token_here
     ```

3. **Create Discord Application:**
   - Go to https://discord.com/developers/applications
   - Create a new application
   - Go to "Bot" section and create a bot
   - Copy the token to your `.env` file
   - Under "OAuth2" > "URL Generator", select "bot" and "applications.commands" scopes
   - Select necessary permissions and invite the bot to your server

4. **Run the bot:**
   ```bash
   # Make sure virtual environment is activated
   source venv/bin/activate
   python -m bot.main
   ```

## Features

- **Slash Commands:** Modern Discord slash commands for all interactions
- **Auto Channel Creation:** Automatically creates `#boss-challenge` channels
- **Progress Tracking:** Users can join events and track their progress
- **Persistent Storage:** Uses TinyDB for lightweight data persistence

## Commands

- `/ping` - Test if the bot is responsive
- `/join` - Join the current event
- `/leave` - Leave the current event
- `/reset` - Reset your progress to 0
- `/complete` - Submit completion with before/after images

## Project Structure

```
boss-challenge/
├── bot/
│   ├── main.py           # Bot entry point
│   ├── cogs/
│   │   └── event.py      # Event commands
│   └── db/
│       └── tiny.py       # Database adapter
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

