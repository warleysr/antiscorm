#!/bin/bash
python3 -m venv .venv
alias activate=". ./.venv/bin/activate"
activate
pip install -r requirements.txt
python3 antiscorm.py