@echo off
python -m venv .venv
call %~dp0.venv\Scripts\activate.bat
pip install -r requirements.txt
python antiscorm.py
pause