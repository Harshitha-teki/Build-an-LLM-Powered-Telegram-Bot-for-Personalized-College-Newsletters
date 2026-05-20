import os
import httpx
from datetime import datetime
from database import SessionLocal, Event, Course

async def get_campus_events():
    db = SessionLocal()
    try:
        events = db.query(Event).all()
        return [{"name": e.name, "description": e.description, "event_date": e.event_date.isoformat()} for e in events]
    finally:
        db.close()

async def get_course_reminders(program: str):
    db = SessionLocal()
    try:
        courses = db.query(Course).all()
        return [{"name": c.name, "reminder": c.reminder, "due_date": c.due_date.isoformat()} for c in courses]
    finally:
        db.close()

async def get_weather_forecast(location: str):
    api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
    if not api_key or api_key == "your_openweathermap_api_key_here":
        # Return mock data if API key is not set or invalid
        return [{"date": datetime.now().isoformat(), "temp": 22.5, "condition": "Sunny"}]
    
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            forecasts = []
            for item in data.get('list', [])[::8]: # Roughly daily
                forecasts.append({
                    "date": item['dt_txt'],
                    "temp": item['main']['temp'],
                    "condition": item['weather'][0]['description']
                })
            return forecasts
    except Exception:
        # Fallback to mock data on error
        return [{"date": datetime.now().isoformat(), "temp": 22.5, "condition": "Sunny"}]

# Tool registry for easy lookup
mcp_tools = {
    "get_campus_events": get_campus_events,
    "get_course_reminders": get_course_reminders,
    "get_weather_forecast": get_weather_forecast
}
