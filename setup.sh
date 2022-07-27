#!/bin/bash
python3 -m venv venv
source venv/bin/activate.csh
pip install -r requirements.txt
python3 antiscorm.py