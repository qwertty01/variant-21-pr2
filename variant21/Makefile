.PHONY: run test clean lint

run:
	./run.sh

test:
	python -m pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -f *.svg *.d2 *.png
	rm -rf .pytest_cache

lint:
	python -m py_compile src/*.py
