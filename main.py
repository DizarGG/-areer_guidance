from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import json
import os

app = FastAPI(title="Профориентация API")
os.makedirs("static", exist_ok=True)

SQLALCHEMY_DATABASE_URL = "sqlite:///./career_test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    scores = Column(Text)
    profile = Column(String)
    energy = Column(Integer, default=0)
    math = Column(Integer, default=0)
    tech = Column(Integer, default=0)
    career = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class TestResult(BaseModel):
    username: str
    scores: dict
    profile: str
    energy: int
    math: int
    tech: int
    career: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_username_exists(username: str, db: Session):
    return db.query(Result).filter(Result.username == username).first() is not None

@app.get("/", response_class=FileResponse)
async def read_root():
    return FileResponse("static/index.html")

@app.get("/api/check_username/{username}")
async def check_username(username: str, db: Session = Depends(get_db)):
    return {"exists": check_username_exists(username, db)}

@app.post("/api/submit")
async def submit_result(result: TestResult, db: Session = Depends(get_db)):
    scores_json = json.dumps(result.scores)
    db_result = Result(
        username=result.username,
        scores=scores_json,
        profile=result.profile,
        energy=result.energy,
        math=result.math,
        tech=result.tech,
        career=result.career
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return {"success": True, "id": db_result.id}

@app.get("/api/results")
async def get_results(username: str | None = None, db: Session = Depends(get_db)):
    if not username:
        return {"results": []}
    results = db.query(Result).filter(Result.username == username).order_by(Result.date.desc()).all()
    response_results = []
    for r in results:
        response_results.append({
            "id": r.id,
            "username": r.username,
            "profile": r.profile,
            "date": r.date.strftime("%d.%m.%Y %H:%M"),
            "energy": r.energy,
            "math": r.math,
            "tech": r.tech,
            "career": r.career
        })
    return {"results": response_results}

