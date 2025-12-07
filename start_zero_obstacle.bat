@echo off
setlocal
echo Demarrage du serveur Zero Obstacle Agents...
call venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8080
