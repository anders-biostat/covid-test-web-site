#!/bin/sh
until nc -z postgres 5432;
  do echo "Waiting for Postgres...";
done;

python manage.py makemigrations
python manage.py migrate --noinput
./superuser.sh &&
python manage.py collectstatic --noinput
gunicorn covidtest.wsgi:application -w 2 -b :8000 --capture-output --log-level=info