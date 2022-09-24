python manage.py migrate
python manage.py collectstatic --noinput
PASS=$?
if [ $PASS == 0 ]; then
  gunicorn --bind 0.0.0.0:"$PORT" -w 4 --limit-request-line 6094 --access-logfile - src.wsgi:application
  else
    echo "Migration or collect static operation failed"
fi
