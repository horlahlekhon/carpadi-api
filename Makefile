clean:
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.log' -delete

db_reset:
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc"  -delete

	python manage.py makemigrations
	python manage.py migrate

install:
	 python virtualenv python3 .
	cd carpadi-api
	pip3 install -r requirements/dev.txt
	./manage.py migrate

test:
	python manage.py test --noinput --parallel=4 #--pdb


shell:
	python manage.py shell_plus


run_stage:
	docker-compose -f docker-compose.yml up --force-recreate

teardown:
	docker-compose -f  docker-compose.yml down --remove-orphans -v

migrate:
	python manage.py makemigrations
	python manage.py migrate

all: clean install run_stage