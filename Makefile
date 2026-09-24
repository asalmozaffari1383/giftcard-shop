PYTHON ?= python

.PHONY: check test test-fast schema migrate worker beat lint

check:
	$(PYTHON) manage.py check
	$(PYTHON) manage.py makemigrations --check --dry-run

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
