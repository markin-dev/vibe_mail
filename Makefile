.PHONY: install dev run lint format remake_db fresh_dev

PIPENV := pipenv run
APP := app.main:app
DB := vide_mail.db

install:
	pipenv install

dev:
	$(PIPENV) uvicorn $(APP) --reload

run:
	$(PIPENV) uvicorn $(APP)

lint:
	$(PIPENV) ruff check

format:
	$(PIPENV) ruff format

remake_db:
	rm -f $(DB)
	$(PIPENV) python seed_campaigns.py

fresh_dev:
	$(MAKE) remake_db
	$(MAKE) dev
