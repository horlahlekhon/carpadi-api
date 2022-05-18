python manage.py migrate
python manage.py collectstatic --noinput
supervisord --nodaemon --configuration ./supervisord.conf