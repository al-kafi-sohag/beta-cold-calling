#!/bin/bash
set -e

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt


uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000