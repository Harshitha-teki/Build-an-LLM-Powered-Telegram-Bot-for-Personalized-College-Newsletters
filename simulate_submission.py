import json
import asyncio
from pathlib import Path

# Ensure we can import the app modules (the container's PYTHONPATH is /app/src)
# This script is intended to be run inside the bot container where /app/src is on PYTHONPATH

async def main():
    try:
        from mcp_tools import get_campus_events, get_course_reminders, get_weather_forecast
        from llm_service import generate_newsletter_section
        from database import SessionLocal, User
    except Exception as e:
        print('Import error:', e)
        return

    cfg = {}
    try:
        with open('submission.json', 'r') as f:
            cfg = json.load(f)
    except Exception as e:
        print('Could not load submission.json:', e)
        return

    test_user = cfg.get('test_user', {})
    if not test_user:
        print('submission.json missing test_user')
        return

    chat_id = int(test_user.get('chat_id'))
    program = test_user.get('program')

    # Ensure user exists in DB
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.chat_id == chat_id).first()
        if not user:
            user = User(chat_id=chat_id, college=test_user.get('college','Unknown'), program=program, is_active=True)
            db.add(user)
            db.commit()
            print(f'Inserted test user {chat_id} into DB')
        else:
            print(f'User {chat_id} already exists in DB')
    finally:
        db.close()

    # Fetch data and generate newsletter sections
    events = await get_campus_events()
    courses = await get_course_reminders(program)
    weather_location = cfg.get('weather_location', 'New York,US')
    weather = await get_weather_forecast(weather_location)

    print('\nGenerating newsletter sections from LLM (may take some seconds)...\n')
    events_text = await generate_newsletter_section('events', events=events)
    courses_text = await generate_newsletter_section('courses', courses=courses, program=program)
    weather_text = await generate_newsletter_section('weather', weather=weather, location=weather_location)

    final_msg = f"*Events This Week*\n{events_text}\n\n*Course Reminders*\n{courses_text}\n\n*Weather Outlook*\n{weather_text}"

    print('\n----- GENERATED NEWSLETTER (MarkdownV2) -----\n')
    print(final_msg)
    print('\n----- END -----\n')

if __name__ == '__main__':
    asyncio.run(main())
