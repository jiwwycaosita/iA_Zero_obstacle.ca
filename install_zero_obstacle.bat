@echo off
setlocal ENABLEDELAYEDEXPANSION

echo === Installation Zero Obstacle Agents (FastAPI + dépendances) ===

REM Vérifier Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python non detecte. Installation via winget...
    winget install -e --id Python.Python.3.12
    if %ERRORLEVEL% NEQ 0 (
        echo Echec installation Python. Installe-le manuellement puis relance ce script.
        pause
        exit /b 1
    )
)

echo.
echo Creation de l'environnement virtuel...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Echec creation venv.
    pause
    exit /b 1
)

echo.
echo Activation de l'environnement et installation des packages...
call venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Creation du fichier .env (OLLAMA_URL et OLLAMA_MODEL) si inexistant...
if not exist ".env" (
    echo OLLAMA_URL=http://localhost:11434> .env
    echo OLLAMA_MODEL=llama3.1>> .env
)

echo.
echo Installation terminee.
echo Pour demarrer le serveur, lance : start_zero_obstacle.bat
pause
