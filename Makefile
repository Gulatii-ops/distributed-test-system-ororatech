.PHONY: help install build up down run test logs ps clean

help:
	@echo "Usage:"
	@echo "  make install    Install dependencies"
	@echo "  make build      Build containers"
	@echo "  make up         Start containers"
	@echo "  make down       Stop containers"
	@echo "  make run        Run dispatcher"
	@echo "  make test       Run full test"
	@echo "  make logs       Show logs"
	@echo "  make ps         Show container status"
	@echo "  make clean      Clean up"

install:
	pip install -r requirements.txt

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

run:
	python dispatch.py

test: build up
	@sleep 2
	python dispatch.py
	@sleep 10
	$(MAKE) down

logs:
	docker-compose logs

ps:
	docker-compose ps

clean:
	docker-compose down -v
	docker system prune -f