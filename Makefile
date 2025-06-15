# Detect OS to pick correct Python path in venv
ifeq ($(OS),Windows_NT)
	VENV_PYTHON := .venv/Scripts/python.exe
else
	VENV_PYTHON := .venv/bin/python
endif

install:
	python3 -m venv .venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt

run:
	$(VENV_PYTHON) quote_generator.py --batch quotes.json

clean:
	rm -rf __pycache__ output/*.png .venv
