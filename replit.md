# Eden Token Assistant

Telegram-based launchpad assistant for pump.fun.

## Overview
- **Backend**: FastAPI (Python)
- **Bot**: Aiogram 3.x
- **Database**: PostgreSQL (SQLAlchemy 2.0)

## Project Structure
- `src/main.py`: FastAPI API Server (Port 5000)
- `src/bot.py`: Telegram Bot Implementation
- `src/models.py`: Database Schema and Models

## Recent Changes
- Initial project setup with FastAPI, Aiogram, and PostgreSQL.
- Configured API Server workflow on port 5000.
- Implemented core bot logic for project creation and pump.fun description generation.
- Set up auto-scaling deployment configuration.

## User Preferences
- Follows standard Python project conventions.
- Uses 0.0.0.0 for frontend/API to allow Replit proxying.
