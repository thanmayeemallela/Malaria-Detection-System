@echo off
title Malaria Detection System - Local Server
echo ============================================================
echo   MALARIA DETECTION SYSTEM - Diploma Project
echo   Starting Local Django Development Server...
echo ============================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run migrations (safe to run repeatedly)
echo [1/3] Applying database migrations...
python manage.py migrate --run-syncdb 2>nul
echo.

REM Create media directories if missing
if not exist "media\blood_smears" mkdir "media\blood_smears"
if not exist "media\reports" mkdir "media\reports"
if not exist "models" mkdir "models"

echo [2/3] Checking model weights...
if exist "models\malaria_classifier.joblib" (
    echo       Trained model found: models\malaria_classifier.joblib
) else (
    echo       WARNING: No trained model found. Run train_model.py first.
)
echo.

echo [3/3] Starting Django development server on http://127.0.0.1:8000
echo.
echo ============================================================
echo   Open your browser and go to:  http://127.0.0.1:8000
echo   Admin panel:                  http://127.0.0.1:8000/admin/
echo   Press Ctrl+C to stop the server.
echo ============================================================
echo.

python manage.py runserver 127.0.0.1:8000
pause
