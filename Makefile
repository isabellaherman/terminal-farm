.PHONY: l f lf

l:
	-poetry run ruff check --fix

f:
	poetry run ruff format

lf: l f
