include .env.dev

ENV_DIR ?= venv
ENV = $(CURDIR)/$(ENV_DIR)
CELERY = $(ENV)/bin/celery
PRECOMMIT = $(ENV)/bin/pre-commit
PIP = $(ENV)/bin/pip
PYTHON3 = $(ENV)/bin/python3
PYTEST = $(ENV)/bin/pytest

DOCKER_FILE ?= docker-compose-developer.yml

define setup_engine_env
	export `grep -v '^#' .env.dev | xargs -0` && cd engine
endef

$(ENV):
	python3.9 -m venv $(ENV_DIR)

bootstrap: $(ENV)
	$(PIP) install -U pip wheel
	cp -n .env.dev.example .env.dev
	cd engine && $(PIP) install -r requirements.txt
	@touch $@

migrate: bootstrap
	$(setup_engine_env) && $(PYTHON3) manage.py migrate

clean:
	rm -rf $(ENV)

lint: bootstrap
	cd engine && $(PRECOMMIT) run --all-files

dbshell: bootstrap
	$(setup_engine_env) && $(PYTHON3) manage.py dbshell $(ARGS)

shell: bootstrap
	$(setup_engine_env) && $(PYTHON3) manage.py shell $(ARGS)

test: bootstrap
	$(setup_engine_env) && $(PYTEST) --ds=settings.dev $(ARGS)

manage: bootstrap
	$(setup_engine_env) && $(PYTHON3) manage.py $(ARGS)

run: bootstrap migrate
	$(setup_engine_env) && $(PYTHON3) manage.py runserver

start-celery: bootstrap
	. $(ENV)/bin/activate && $(setup_engine_env) && $(PYTHON3) manage.py start_celery

start-celery-beat: bootstrap
	$(setup_engine_env) && $(CELERY) -A engine beat -l info

purge-queues: bootstrap
	$(setup_engine_env) && $(CELERY) -A engine purge

docker-services-start:
	docker-compose -f $(DOCKER_FILE) up -d
	@echo "Waiting for database connection..."
	until $$(nc -z -v -w30 localhost 3306); do sleep 1; done;

docker-services-restart:
	docker-compose -f $(DOCKER_FILE) restart

docker-services-stop:
	docker-compose -f $(DOCKER_FILE) stop

watch-plugin:
	cd grafana-plugin && yarn install && yarn && yarn watch

.PHONY: grafana-plugin
