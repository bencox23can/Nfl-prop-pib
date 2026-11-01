#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
printf '\nOpen on your phone: http://YOUR-COMPUTER-LAN-IP:8501\n'
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
