#!/bin/bash
# Changing to the script directory
cd "$(dirname "$0")"


echo 'Reinstalling common package ...'
pip install --force-reinstall --no-cache-dir ./common

echo 'Update and compile translations ...'
cd src/
flask translate update
flask translate compile

# Changing to the script directory
cd ..

echo 'Collect staticfiles from lab tool ...'
cd lab/
python manage.py collectstatic