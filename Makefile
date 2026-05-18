.PHONY: build install lint test clean

IMAGE ?= tfa-claudio:latest
CONTAINER_ENGINE ?= podman

build:
	$(CONTAINER_ENGINE) build -f Containerfile.claudio -t $(IMAGE) .

install:
	pip install -r requirements.txt

lint:
	shellcheck tools/common.sh skills/*/scripts/*.sh
	python -m py_compile tools/rp-client/rp_client.py
	python -m py_compile tools/must-gather/must_gather_parser.py

test:
	python -m pytest tests/ -v

clean:
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -delete
