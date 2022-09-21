python manage.py migrate
python manage.py collectstatic --noinput
gunicorn --bind 0.0.0.0:"$PORT" -w 4 --limit-request-line 6094 --access-logfile - src.wsgi:application
