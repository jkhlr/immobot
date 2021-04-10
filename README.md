# immobot

Scrape immobilienscout24.de and receive new results through a Telegram bot

## Usage
- Create an empty `.env` file and an empty `db.sqlite3` file in the project root
- Create a telegram bot, and add the API token as `IMMOBOT_TELEGRAM_API_TOKEN` to the `.env` file
- Run `docker-compose up`
- Open a new chat with the telegram bot you created (can be a private chat, or you can add the bot to a group).
- Write `/watch [URL]`, to make the bot watch a search query on immobilienscout24.de, providing the URL to the first page of the search results.
- Be careful with the bot detection. If the bot gets detected, set `IMMOBOT_SCRAPE_INTERVAL_SECONDS` (how often the search page is scraped) or `IMMOBOT_REQUEST_PAUSE_SECONDS` (time between requests to each page of a search result) to higher values (defaults can be found in settings.py) throug the `.env` file (and run `docker-compose up` afterwards, to restart the bot). If you get blocked, you might have to wait for an hour or so, until your IP gets unblocked again.
- Have fun with your new home :)