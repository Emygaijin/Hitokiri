#!/bin/bash
set -e  # This ensures the script exits immediately if a command fails

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
