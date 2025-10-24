@echo off
REM Change directory to the folder of this script
cd /d %~dp0

REM Start FastAPI server hidden
start "" /min python -m uvicorn main:app --reload

REM Wait a few seconds for the server to start
timeout /t 5 /nobreak > nul

REM Open Swagger UI in default browser
start "" http://127.0.0.1:8000/docs
