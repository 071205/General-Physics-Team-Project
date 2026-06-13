@echo off
cd /d "%~dp0"
echo Installing required Python package...
py -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo The 'py' command failed. Trying 'python' instead...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Python could not be started. Install Python 3 and try again.
        pause
        exit /b 1
    )
    python spool_simulation.py
) else (
    py spool_simulation.py
)
pause
