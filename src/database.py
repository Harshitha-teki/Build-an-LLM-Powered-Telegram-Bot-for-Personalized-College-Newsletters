import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker

# Handle path correctly for SQLite
db_url = os.getenv("DATABASE_URL", "sqlite:///data/newsletter.db")
if db_url.startswith("sqlite:///"):
    db_path = db_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

engine = create_engine(db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    college = Column(String, nullable=False)
    program = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    event_date = Column(DateTime, nullable=False)

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    reminder = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    seed_db()

def seed_db():
    db = SessionLocal()
    try:
        if db.query(Event).first() is None:
            events = [
                Event(name="Tech Talk: AI in 2026", description="Join us for a discussion on the future of AI.", event_date=datetime.now() + timedelta(days=1)),
                Event(name="Career Fair", description="Meet with top tech companies.", event_date=datetime.now() + timedelta(days=2)),
                Event(name="Hackathon Kickoff", description="Start building your next big idea.", event_date=datetime.now() + timedelta(days=3)),
                Event(name="Alumni Mixer", description="Network with successful graduates.", event_date=datetime.now() + timedelta(days=4)),
                Event(name="Campus Concert", description="Live music on the quad.", event_date=datetime.now() + timedelta(days=5)),
            ]
            db.add_all(events)
        
        if db.query(Course).first() is None:
            courses = [
                Course(name="CS 101", reminder="Assignment 1 due", due_date=datetime.now() + timedelta(days=1)),
                Course(name="CS 201", reminder="Midterm Project", due_date=datetime.now() + timedelta(days=2)),
                Course(name="Math 101", reminder="Quiz 3", due_date=datetime.now() + timedelta(days=3)),
                Course(name="Physics 101", reminder="Lab Report", due_date=datetime.now() + timedelta(days=4)),
                Course(name="History 101", reminder="Essay Outline", due_date=datetime.now() + timedelta(days=5)),
            ]
            db.add_all(courses)
        db.commit()
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
