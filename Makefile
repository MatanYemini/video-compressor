.PHONY: install install-ffmpeg install-requirements help

help:
	@echo "Available commands:"
	@echo "  make install         - Install ffmpeg and Python requirements"
	@echo "  make install-ffmpeg  - Install only ffmpeg"
	@echo "  make help            - Show this help message"

install: install-ffmpeg

install-ffmpeg:
	@echo "Checking operating system..."
	@if [ "$$(uname)" = "Darwin" ]; then \
		echo "Installing ffmpeg using Homebrew (macOS)..."; \
		if ! command -v brew >/dev/null 2>&1; then \
			echo "Homebrew not found. Please install Homebrew first: https://brew.sh/"; \
			exit 1; \
		fi; \
		brew install ffmpeg; \
	elif [ "$$(uname)" = "Linux" ]; then \
		echo "Installing ffmpeg (Linux)..."; \
		if command -v apt-get >/dev/null 2>&1; then \
			sudo apt-get update && sudo apt-get install -y ffmpeg; \
		elif command -v yum >/dev/null 2>&1; then \
			sudo yum install -y ffmpeg; \
		elif command -v dnf >/dev/null 2>&1; then \
			sudo dnf install -y ffmpeg; \
		elif command -v pacman >/dev/null 2>&1; then \
			sudo pacman -S ffmpeg; \
		else \
			echo "Unsupported package manager. Please install ffmpeg manually."; \
			exit 1; \
		fi; \
	elif [ "$$(uname)" = "Windows_NT" ] || [ "$$(uname -s | cut -c 1-5)" = "MINGW" ]; then \
		echo "On Windows, please install ffmpeg manually:"; \
		echo "1. Download from https://www.gyan.dev/ffmpeg/builds/"; \
		echo "2. Extract and add the bin directory to your PATH"; \
	else \
		echo "Unsupported operating system. Please install ffmpeg manually."; \
		exit 1; \
	fi
	@echo "Checking if ffmpeg is installed..."
	@if command -v ffmpeg >/dev/null 2>&1; then \
		echo "ffmpeg is installed successfully."; \
	else \
		echo "ffmpeg installation failed or not in PATH. Please install manually."; \
		exit 1; \
	fi 