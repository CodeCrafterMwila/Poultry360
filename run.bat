@echo off
TITLE Poultry360 - Smart Broiler Farm Management
CLS

echo ==================================================
echo   Poultry360 - Smart Broiler Farm Management 🐔
echo ==================================================
echo.

REM Check if venv exists, if not create it using Python 3.12
if not exist venv (
    echo [*] Creating Python 3.12 virtual environment...
    C:\Users\asus\AppData\Local\Programs\Python\Python312\python.exe -m venv venv
)

echo [*] Activating virtual environment...
call venv\Scripts\activate

echo [*] Upgrading pip and installing requirements...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt

echo.
echo [*] Launching Poultry360 Streamlit Application...
echo ==================================================
streamlit run app.py

pause