# Dictionary Bot

A Telegram bot (aiogram 3) where users submit a photo + caption "note",
an admin moderates it, and approved notes can be browsed randomly or
paged through with per-note reactions.

## Structure

```
bot/
  main.py                   entry point: builds Bot/Dispatcher, starts polling
  config.py                 env-based settings (BOT_TOKEN, ADMIN_IDS, DB_PATH)
  handlers/
    user/
      start.py               /start + main menu
      upload.py               FSM: submit a photo+caption note
      browse.py                random note / paginated all-notes
      reactions.py            reaction button callbacks
    admin/
      moderation.py           approve / reject / add-note review queue
  keyboards/
    user_kb.py                reply menu, reaction row, nav buttons
    admin_kb.py                moderation buttons
  states/                     FSM state groups
  database/
    models.py                 User, Note, Reaction (SQLAlchemy 2.0)
    engine.py                 async engine/session, init_db()
    repositories/              DB access, one module per model
  middlewares/db_session.py   injects a DB session into every update
  filters/is_admin.py         restricts admin router to ADMIN_IDS
  utils/pagination.py         helpers for the "all notes" nav
tests/
data/                         SQLite file lives here (gitignored)
```

Handlers are intentionally left with `TODO` markers instead of full
logic — the wiring (routers, FSM states, keyboards, DB schema,
middleware) is in place so you can fill in one file at a time without
having to first figure out where things go.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate        # .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env             # fill in BOT_TOKEN and ADMIN_IDS
python -m bot.main
```

## Docker

```bash
cp .env.example .env             # fill in BOT_TOKEN and ADMIN_IDS
docker compose up --build
```

The SQLite file is written to `./data/dictionary.db` on the host via
the volume mount in `docker-compose.yml`, so it survives rebuilds.

## Design notes

- **Photos aren't downloaded or stored anywhere** — only Telegram's
  `file_id` is saved. Telegram keeps hosting the actual image.
- **One reaction per user per note**, enforced by a unique constraint
  on `(note_id, user_id)`. Repeat-tapping the same reaction removes it;
  tapping a different one replaces it.
- **Repository pattern**: handlers never touch SQLAlchemy directly,
  they call functions in `database/repositories/`. Keeps handlers thin
  and makes the DB layer independently testable.
- **SQLite now, Postgres later if needed**: nothing above is
  SQLite-specific except `DB_PATH`/`DB_URL` in `config.py` — switching
  later is a connection-string + driver change, not a rewrite.
