PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON = $(VENV)/bin/python

test:
	./run-tests.sh baseline

test-unit:
	./run-tests.sh unit

test-lab:
	./run-tests.sh lab

test-full:
	./run-tests.sh full

clean:
	rm -f -r build/
	rm -f -r dist/
	rm -f -r *.egg-info
	rm -f -r rust/target/
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f  {} +

publish: clean package
	$(VENV_PYTHON) -m twine check dist/*
	$(VENV_PYTHON) -m twine upload dist/*

package: clean $(VENV_PYTHON)
	@$(VENV_PYTHON) -c "import build" 2>/dev/null || $(VENV_PYTHON) -m pip install build
	$(VENV_PYTHON) -m build --config-setting=--build-option=--py-limited-api=cp311

rebuild: clean
	$(PYTHON) -m pip install --force-reinstall .

build:
	$(PYTHON) -m pip install --editable .

$(VENV_PYTHON):
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip build twine
