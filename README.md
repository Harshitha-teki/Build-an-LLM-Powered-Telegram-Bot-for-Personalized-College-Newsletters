# LLM-Powered Telegram Bot for Personalized College Newsletters

This project implements a Telegram bot backed by a local Ollama LLM to synthesize and send customized college newsletters.

## Architecture

- **Database**: SQLite with SQLAlchemy (`data/newsletter.db`)
- **LLM**: Local Ollama instance (`llama3.1:8b`)
- **Web/API**: FastAPI exposing `POST /test-mcp-tool`
- **Bot Engine**: `python-telegram-bot`
- **Scheduler**: `APScheduler`

## Setup Instructions

1. Copy `.env.example` to `.env` (optional, since docker-compose uses `.env.example` for evaluation as per instructions, but you can override).
2. Configure `TELEGRAM_BOT_TOKEN` and `OPENWEATHERMAP_API_KEY`.
3. Run `docker-compose up --build -d`.

This will start the Ollama service, pull the required model, and then start the bot service.

## Evaluation Endpoints

A test endpoint is available at `http://localhost:8000/test-mcp-tool`.
Example payload:
```json
{
  "tool_name": "get_weather_forecast",
  "tool_args": {"location": "New York,US"}
}
```
