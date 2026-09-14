@echo off
title Gemma Studio Launcher
color 0A

echo ===================================================
echo               KHOI DONG GEMMA STUDIO
echo ===================================================
echo.

:: 1. Chuyen huong ve thu muc du an
cd /d "D:\GemmaTraining"

:: 2. Kich hoat moitruong ao Python (.venv)
call .venv\Scripts\activate.bat

:: 3. Chuyen vao thu muc app
cd app

:: 4. Tu dong mo trinh duyet sau 3 giay (chay ngam)
start "" cmd /c "timeout /t 3 >nul && start http://127.0.0.1:8000"

:: 5. Khoi chay Uvicorn Server
echo [INFO] Dang khoi chay Uvicorn Server tai http://127.0.0.1:8000 ...
echo [INFO] Nhan Ctrl + C trong cua so nay neu muon tat Server.
echo.
uvicorn web:app --host 127.0.0.1 --port 8000

pause