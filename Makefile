run:
	python manage.py runserver

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

makesuperuser:
	python manage.py createsuperuser --username tytar --email tytarenko.sergey@gmail.com

clean:
	find . -name "*.pyc" -exec rm -rf {} \;

shell:
	python manage.py shell_plus

dumpfixtuser:
	python manage.py dumpdata --format=json base > base/fixtures/initial_data.json

resetdb:
	python manage.py reset_db && python manage.py migrate && python manage.py filldata
