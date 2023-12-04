#
# File: 		Makefile
# Description:  When run with `make`, this provides tools for using and developing the `anaconda_packaging_utils` project

# The `.ONESHELL` and setting `SHELL` allows us to run commands that require `conda activate`
.ONESHELL:
SHELL := /bin/bash
# For GNU Make v4 and above, you must include the `-c` in order for `make` to find symbols from `PATH`
.SHELLFLAGS := -c -o pipefail -o errexit
CONDA_ACTIVATE = source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
# Ensure that we are using the python interpretter provided by the conda environment.
PYTHON3 := "$(CONDA_PREFIX)/bin/python3"

.PHONY: clean clean-cov clean-build clean-env clean-pyc clean-test help pre-commit test test-cov lint format format-docs analyze
.DEFAULT_GOAL := help

CONDA_ENV_NAME ?= anaconda-packaging-utils

# `BROWSER_PYSCRIPT` and `PRINT_HELP_PYSCRIPT` are used to generate the output
# of `make help` automatically. This requires each `make` directive to be
# followed by a `##` comment with a description.
define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := $(PYTHON3) -c "$$BROWSER_PYSCRIPT"

clean: clean-build clean-cov clean-env clean-pyc clean-test	## remove all build, test, coverage, environment and Python artifacts

clean-cov:					## remove code coverage artifacts
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf reports/{*.html,*.png,*.js,*.css,*.json}
	rm -rf pytest.xml
	rm -rf pytest-coverage.txt

clean-build: 				## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-env:					## remove conda environment
	conda remove -y -n $(CONDA_ENV_NAME) --all

clean-pyc: 					## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: 				## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

environment:       			## handles environment creation
	conda env create -f environment.yaml --name $(CONDA_ENV_NAME) --force
	conda run --name $(CONDA_ENV_NAME) pip install .

help:
	$(PYTHON3) -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

pre-commit:					## runs pre-commit against files
	pre-commit run --all-files

install: clean 				## install the package to the active (current environment's) Python's site-packages
	pip install .

dev: clean					## install the package's development version to a fresh environment
	conda env create -f environment.yaml --name $(CONDA_ENV_NAME) --force
	conda run --name $(CONDA_ENV_NAME) pip install -e .
	$(CONDA_ACTIVATE) $(CONDA_ENV_NAME) && pre-commit install

test:						## executes unit test cases
	$(PYTHON3) -m pytest -n auto --capture=no anaconda_packaging_utils/tests/

test-debug:		## runs test cases with debugging info enabled
	$(PYTHON3) -m pytest -n auto -vv --capture=no anaconda_packaging_utils/tests/

test-cov:					## checks test coverage requirements
	$(PYTHON3) -m pytest -n auto --cov-config=.coveragerc --cov=anaconda_packaging_utils \
		anaconda_packaging_utils/tests/ --cov-fail-under=80 --cov-report term-missing

lint:						## runs the linter against the project
	pylint --rcfile=.pylintrc anaconda_packaging_utils

format:						## runs the code auto-formatter
	isort --profile black --line-length=120 anaconda_packaging_utils
	black --line-length=120 anaconda_packaging_utils

format-docs:	## runs the docstring auto-formatter. Note this requires manually installing `docconvert`
	docconvert --in-place --config .docconvert.json anaconda_packaging_utils

analyze:					## runs static analyzer on the project
	mypy --config-file=.mypy.ini --cache-dir=/dev/null anaconda_packaging_utils/
