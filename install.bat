@echo off
REM Simple installation script for Windows.
IF NOT EXIST ".venv" (
    python -m venv .venv
)
CALL .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo Installation complete. Activate the virtual environment with:
echo   call .venv\Scripts\activate.bat
echo Then run autovideo --help to see available commands.