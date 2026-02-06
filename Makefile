# Variables
VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip
PYINSTALLER = $(VENV)/bin/pyinstaller
APP_NAME = ZettelCompose

PYINSTALLER = $(PYTHON) -m PyInstaller

.PHONY: all install clean bundle help

all: help

help:
	@echo "Available commands:"
	@echo "  make install  - Create venv and install dependencies"
	@echo "  make bundle   - Create a standalone macOS .app bundle"
	@echo "  make clean    - Remove build artifacts and venv"

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

install: $(VENV)/bin/activate

bundle: install
	@echo "Building macOS Bundle..."
	$(PYINSTALLER) --noconfirm --onefile --windowed \
		--name $(APP_NAME) \
		--collect-all bleak \
		--hidden-import bleak.backends.macos.backend \
		zettel-compose.py
	@echo "Bundle created at dist/$(APP_NAME).app"

clean:
	rm -rf $(VENV) build dist
	rm -f *.spec
	find . -type d -name "__pycache__" -exec rm -rf {} +

