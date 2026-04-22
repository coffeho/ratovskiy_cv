.PHONY: create-structure install-dep install test-pytest test

create-structure:
	mkdir -p src tests docs
	touch src/.gitkeep tests/.gitkeep
	touch docs/DOMAIN.md README.md .gitignore setup.py requirements.txt

install-dep:
	pip install -r requirements.txt

install:
	pip install -e .

test-pytest:
	python3 -m pytest

test: install-dep install test-pytest