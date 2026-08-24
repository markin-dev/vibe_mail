.PHONY: dev run install

install:
	pipenv install

dev:
	pipenv run uvicorn app.main:app --reload

run:
	pipenv run uvicorn app.main:app
