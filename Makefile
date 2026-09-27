PYTHON ?= python

.PHONY: check production-check production-check-live test test-fast schema migrate worker beat lint

check:
	$(PYTHON) manage.py check
	$(PYTHON) manage.py makemigrations --check --dry-run

production-check:
	$(PYTHON) manage.py check --deploy
	$(PYTHON) manage.py production_check

production-check-live:
	$(PYTHON) manage.py check --deploy
	$(PYTHON) manage.py production_check --live

test:
	$(PYTHON) manage.py test

test-fast:
	DJANGO_SETTINGS_MODULE=config.settings_test $(PYTHON) manage.py test

schema:
	$(PYTHON) manage.py spectacular --validate --file schema.yaml

migrate:
	$(PYTHON) manage.py migrate

worker:
	celery -A config worker -l info

beat:
	celery -A config beat -l info

lint:
	ruff check .
