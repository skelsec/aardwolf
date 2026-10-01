PYTHON ?= python3

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
	$(PYTHON) -m twine check dist/*
	$(PYTHON) -m twine upload dist/*

package: clean
	$(PYTHON) -m build --config-setting=--build-option=--py-limited-api=cp311

rebuild: clean
	$(PYTHON) -m pip install --force-reinstall .

build:
	$(PYTHON) -m pip install --editable .
