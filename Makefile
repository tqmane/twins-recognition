PYTHON?=.venv/bin/python
PIP?=.venv/bin/pip

.PHONY: venv install dev cli gui test clean

venv:
	python3 -m venv .venv
	$(PIP) install -U pip

install: venv
	$(PIP) install -e .

dev: install
	$(PIP) install pytest

cli:
	PYTHONPATH=src $(PYTHON) -m twins_recognition.cli --help

gui:
	$(PYTHON) -m twins_recognition.gui

test:
	$(PYTHON) -m pytest -q

clean:
	rm -rf .venv build dist *.egg-info