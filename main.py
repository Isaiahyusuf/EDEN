import os
import asyncio
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from models import init_db, get_session, User, Project


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Eden Token Assistant API",
    description="API for Eden Token Assistant - Telegram-based launchpad assistant for pump.fun",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProjectResponse(BaseModel):
    id: int
    token_name: Optional[str]
    token_symbol: Optional[str]
    description: Optional[str]
    status: str
    website: Optional[str]
    twitter: Optional[str]


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]


class HealthResponse(BaseModel):
    status: str
    message: str


@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="ok",
        message="Eden Token Assistant API is running"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    session = get_session()
    if session:
        session.close()
        return HealthResponse(status="ok", message="Database connected")
    return HealthResponse(status="degraded", message="Database not available")


@app.get("/api/users/{telegram_id}", response_model=UserResponse)
async def get_user(telegram_id: int):
    session = get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database not available")
    
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name
    )


@app.get("/api/users/{telegram_id}/projects", response_model=List[ProjectResponse])
async def get_user_projects(telegram_id: int):
    session = get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database not available")
    
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    projects = session.query(Project).filter(Project.owner_id == user.id).all()
    
    return [
        ProjectResponse(
            id=p.id,
            token_name=p.token_name,
            token_symbol=p.token_symbol,
            description=p.description,
            status=p.status,
            website=p.website,
            twitter=p.twitter
        )
        for p in projects
    ]


@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    session = get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database not available")
    
    project = session.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(
        id=project.id,
        token_name=project.token_name,
        token_symbol=project.token_symbol,
        description=project.description,
        status=project.status,
        website=project.website,
        twitter=project.twitter
    )


@app.get("/api/stats")
async def get_stats():
    session = get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database not available")
    
    total_users = session.query(User).count()
    total_projects = session.query(Project).count()
    launched_projects = session.query(Project).filter(Project.status == "launched").count()
    
    return {
        "total_users": total_users,
        "total_projects": total_projects,
        "launched_projects": launched_projects
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=False
    )
