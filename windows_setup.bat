@echo off
python -m venv venv
call %~dp0venv\Scripts\activate.bat
pip install -r requirements.txt
python antiscorm.py
pause