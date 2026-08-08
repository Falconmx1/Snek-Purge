.PHONY: install uninstall clean test help

help:
	@echo "Comandos disponibles:"
	@echo "  make install    - Instalar Snek-Purge"
	@echo "  make uninstall  - Desinstalar Snek-Purge"
	@echo "  make clean      - Limpiar archivos temporales de Python"
	@echo "  make test       - Ejecutar en modo dry-run"

install:
	pip install -r requirements.txt
	pip install -e .
	@echo "✅ Snek-Purge instalado correctamente"
	@echo "Ejecuta: snek-purge --help"

uninstall:
	pip uninstall snek-purge -y
	@echo "✅ Snek-Purge desinstalado"

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete
	rm -rf build/ dist/ .pytest_cache/
	@echo "✅ Archivos temporales limpiados"

test:
	python snek-purge.py --dry-run --verbose
