# Dictionary Bot

A Telegram bot (aiogram 3) where users submit a photo + caption "note",
an admin moderates it, and approved notes can be browsed randomly or
paged through with per-note reactions, optionally bot sends approved notes
to configured announcement channel

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate        # .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env             # fill in BOT_TOKEN and ADMIN_IDS, (Optionally) ANNOUNCEMENT_CHANNEL
python -m bot.main
```

Note that on windows `source .venv/bin/activate` may not work,
use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` to bypass it

## Docker

```bash
cp .env.example .env             # fill in BOT_TOKEN, ADMIN_IDS, (Optionally) ANNOUNCEMENT_CHANNEL
docker compose up --build
```

Note that if configuring `ANNOUNCEMENT_CHANNEL`, bot must be added to that
channel and allowed to send messages

The SQLite file is written to `./data/dictionary.db` on the host via
the volume mount in `docker-compose.yml`, so it survives rebuilds.

## Bot setup

Bot also supports `/commands` so you can set them up in @BotFather like so

```
start - show the main menu
help - show guide
submit - upload notes
language - select language
random - show random note
browse - browse notes
```

## Structure

```
bot/
  main.py                   entry point: builds Bot/Dispatcher, starts polling
  config.py                 env-based settings (BOT_TOKEN, ADMIN_IDS, DB_PATH, DEFAULT_LANGUAGE)
  dictionaries/
    en.py                   English language pack
    ru.py                   Russian language pack
  handlers/
    user/
      start.py              /start + main menu
      upload.py              FSM: submit a photo+caption note
      browse.py              random note / paginated all-notes
      reactions.py           reaction button callbacks
      language.py            language selection handler
      fallback.py            unknown message handler
    admin/
      moderation.py          approve / reject / add-note review queue
  keyboards/
    user_kb.py               reply menu, reaction row, nav buttons, language selection
    admin_kb.py              moderation buttons
  states/
    upload_states.py         FSM state groups for upload
    admin_states.py          FSM state groups for admin moderation
  database/
    models.py                User, Note, Reaction, Notification (SQLAlchemy 2.0)
    engine.py                async engine/session, init_db()
    repositories/
      user_repo.py           DB access for users
      note_repo.py           DB access for notes
      reaction_repo.py       DB access for reactions
      notification_repo.py   DB access for notifications
      language_repo.py       DB access for language preferences
  middlewares/
    db_session.py            injects a DB session into every update
  filters/
    is_admin.py              restricts admin router to ADMIN_IDS
  utils/
    pagination.py            helpers for the "all notes" nav
    locale.py                user language detection
data/
  dictionary.db             SQLite database file (gitignored)
```

## Design notes

- **Photos aren't downloaded or stored anywhere** — only Telegram's
  `file_id` is saved. Telegram keeps hosting the actual image.
- **One reaction per user per note**, enforced by a unique constraint
  on `(note_id, user_id)`. Repeat-tapping the same reaction removes it;
  tapping a different one replaces it.
- **Repository pattern**: handlers never touch SQLAlchemy directly,
  they call functions in `database/repositories/`. Keeps handlers thin
  and makes the DB layer independently testable.
