install:
	pipenv install

dev:
	pipenv run uvicorn app.main:app --reload

run:
	pipenv run uvicorn app.main:app

lint:
	pipenv run ruff check

format:
	pipenv run ruff format
