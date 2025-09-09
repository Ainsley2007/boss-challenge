---

## alwaysApply: true

# Discord Event Bot — Cursor Roadmap

A lightweight plan for a 1‑week event bot in Python. Use this as guidance in Cursor.

---

## Phase 0 — Setup

* Use **discord.py v2+** with `app_commands` for slash commands.
* Install deps: `pip install discord.py python-dotenv tinydb`
* Project structure:

  ```text
  event_bot/
  ├─ bot/
  │  ├─ main.py
  │  ├─ cogs/event.py
  │  └─ db/tiny.py
  ├─ .env
  └─ README.md
  ```
* `.env` contains:

  ```env
  DISCORD_TOKEN=...
  ```

---

## Phase 1 — Boot & Channel

* Bring bot online with `/ping`.
* On startup: ensure `#event-leaderboard` exists in every guild, create if missing.

---

## Phase 2 — Database Layer (TinyDB)

* `participants`: { guild\_id, user\_id, progress }
* `submissions`: { guild\_id, user\_id, step, before\_url, after\_url, ts }
* API functions:

  * `is_joined(guild_id, user_id)`
  * `join_user(guild_id, user_id)`
  * `leave_user(guild_id, user_id)`
  * `reset_user(guild_id, user_id)`
  * `add_completion(guild_id, user_id, before_url, after_url)`

---

## Phase 3 — Slash Commands

* `/join` → add user to participants.
* `/leave` → remove user.
* `/reset` → reset progress to 0.
* `/complete before:<image> after:<image>` → requires two attachments; increments progress; stores submission.

Rules:

* Commands are idempotent (safe if repeated).
* Replies ephemeral when possible.
* Validate that both attachments are images.

---

## Phase 4 — Leaderboard (later)

* Placeholder: single pinned message in `#event-leaderboard`.
* Later: show ranking by `progress` (tie‑breaker: earliest timestamp).

---

## Cursor Conventions

style:
python:
functions: snake\_case
imports: grouped\_std\_thirdparty\_local
comments: avoid; code should be self‑documenting
discord:
library: discord.py v2+
slash: prefer app\_commands with guild sync
responses: ephemeral for confirmations, embeds for leaderboard

conventions:

* keep commands short (<80 LOC)
* explicit input validation
* idempotent operations
* avoid global state (use db adapter)

scaffolds:

* name: main.py
  path: bot/main.py
  description: Entry point, loads cog, ensures leaderboard channel, syncs commands
* name: event\_cog
  path: bot/cogs/event.py
  description: Slash commands (/join, /leave, /reset, /complete)
* name: db\_adapter
  path: bot/db/tiny.py
  description: TinyDB adapter with required API

---

## Done Criteria

* Bot runs & responds to commands.
* `#event-leaderboard` channel auto‑created.
* Users can join, leave, complete, reset.
* Submissions persist in TinyDB.
* Leaderboard stub exists for later work.
