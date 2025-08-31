# Random Contest Telegram Mini App Bot

Collect contest participants via Telegram Mini App and store them in SQLite (persisted via Docker volume).

## Features
- Telegram bot with /start and Mini App button
- Mini App page posts `web_app_data` back to the bot
- FastAPI web server with static page and health endpoint
- SQLite DB with SQLAlchemy, persisted on a Docker volume

## Tech Stack
- Python 3.11, aiogram 3, FastAPI, SQLAlchemy 2
- Docker, Docker Compose

## Configuration
Create a `.env` file (refer to `env.example`):

```
BOT_TOKEN=your_telegram_bot_token_here
WEBAPP_URL=http://localhost:8000
DATABASE_URL=sqlite:////app/data/app.db
LOG_LEVEL=INFO
```

- `WEBAPP_URL` should be the public URL of your web service when deployed.
- By default the DB path is `/app/data/app.db` which is persisted via volume.

## Run Locally (Docker)

Build images:

```
docker compose build
```

Start services:

```
docker compose up -d
```

- Web: http://localhost:8000
- Bot: runs polling and responds to `/start`

## Development (without Docker)

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BOT_TOKEN=...; export WEBAPP_URL=http://localhost:8000; export DATABASE_URL=sqlite:///./app.db
uvicorn app.web.main:app --reload
python -m app.bot.main
```

## Notes
- Ensure the bot domain is allowed to load the Mini App.
- Data persists across restarts thanks to the `app_data` volume. 