import os
import json
import re
from telegram import Update
from telegram.ext import ContextTypes
from database import SessionLocal, User
from mcp_tools import get_campus_events, get_course_reminders, get_weather_forecast
from llm_service import generate_newsletter_section

def escape_mdv2(text: str) -> str:
    # Escape reserved characters for MarkdownV2, except asterisks which we might use for bolding if the LLM outputted them.
    # However, to be safe, we just escape everything the LLM outputs and manually format our headers.
    escape_chars = r'_[]()~`>#+-=|{}.!*'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.chat_id == chat_id).first()
        if not user:
            college = "Unknown"
            program = "Unknown"
            try:
                with open("submission.json", "r") as f:
                    config = json.load(f)
                    if str(config.get("test_user", {}).get("chat_id")) == str(chat_id):
                        college = config["test_user"]["college"]
                        program = config["test_user"]["program"]
            except Exception:
                pass

            user = User(chat_id=chat_id, college=college, program=program, is_active=True)
            db.add(user)
            db.commit()
            await update.message.reply_text("Welcome! You are now registered for the personalized college newsletter.")
        else:
            user.is_active = True
            db.commit()
            await update.message.reply_text("Welcome back! Your subscription is active again.")
    except Exception as e:
        print(f"Error in start: {e}")
        await update.message.reply_text("An error occurred during registration.")
    finally:
        db.close()

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.chat_id == chat_id).first()
        if user:
            user.is_active = False
            db.commit()
            await update.message.reply_text("You have been unsubscribed from the newsletter.")
        else:
            await update.message.reply_text("You are not registered.")
    except Exception as e:
        print(f"Error in unsubscribe: {e}")
    finally:
        db.close()

async def newsletter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = SessionLocal()
    user = None
    try:
        user = db.query(User).filter(User.chat_id == chat_id).first()
    finally:
        db.close()

    if not user or not user.is_active:
        await update.message.reply_text("You must be registered and active to receive a newsletter. Type /start.")
        return

    await update.message.reply_text("Generating your personalized newsletter... This might take a minute.")
    
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

        await update.message.reply_text(final_msg, parse_mode='MarkdownV2')
    except Exception as e:
        print(f"Error generating newsletter: {e}")
        await update.message.reply_text("Sorry, there was an error generating your newsletter.")
