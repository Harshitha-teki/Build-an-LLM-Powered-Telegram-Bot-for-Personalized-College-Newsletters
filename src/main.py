import os
import json
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from telegram.ext import Application, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import init_db, SessionLocal, User
from bot_handlers import start, unsubscribe, newsletter
from mcp_tools import mcp_tools
from llm_service import generate_newsletter_section
from mcp_tools import get_campus_events, get_course_reminders, get_weather_forecast

app = FastAPI()

class ToolRequest(BaseModel):
    tool_name: str
    tool_args: dict

@app.post("/test-mcp-tool")
async def test_mcp_tool(req: ToolRequest):
    if req.tool_name not in mcp_tools:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    tool_func = mcp_tools[req.tool_name]
    try:
        result = await tool_func(**req.tool_args)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def send_weekly_newsletter():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "your_telegram_bot_token_here":
        return
    
    from telegram import Bot
    from telegram.constants import ParseMode
    from bot_handlers import escape_mdv2
    
    bot = Bot(token)
    db = SessionLocal()
    try:
        active_users = db.query(User).filter(User.is_active == True).all()
        for user in active_users:
            try:
                events = await get_campus_events()
                courses = await get_course_reminders(user.program)
                
                location = "New York,US"
                try:
                    with open("submission.json", "r") as f:
                        config = json.load(f)
                        location = config.get("weather_location", location)
                except Exception:
                    pass
                
                weather = await get_weather_forecast(location)

                events_text = await generate_newsletter_section("events", events=events)
                courses_text = await generate_newsletter_section("courses", courses=courses, program=user.program)
                weather_text = await generate_newsletter_section("weather", weather=weather, location=location)

                final_msg = f"*Events This Week*\n{escape_mdv2(events_text)}\n\n"
                final_msg += f"*Course Reminders*\n{escape_mdv2(courses_text)}\n\n"
                final_msg += f"*Weather Outlook*\n{escape_mdv2(weather_text)}"

                await bot.send_message(chat_id=user.chat_id, text=final_msg, parse_mode=ParseMode.MARKDOWN_V2)
            except Exception as e:
                print(f"Failed to send weekly newsletter to {user.chat_id}: {e}")
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    init_db()
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_weekly_newsletter, 'cron', day_of_week='sun', hour=18)
    scheduler.start()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token and token != "your_telegram_bot_token_here":
        application = Application.builder().token(token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("unsubscribe", unsubscribe))
        application.add_handler(CommandHandler("newsletter", newsletter))
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        app.state.telegram_app = application
    else:
        print("Warning: TELEGRAM_BOT_TOKEN not configured. Bot polling disabled.")

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "telegram_app"):
        await app.state.telegram_app.updater.stop()
        await app.state.telegram_app.stop()
        await app.state.telegram_app.shutdown()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
