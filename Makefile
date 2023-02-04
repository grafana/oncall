DOCKER_COMPOSE_FILE = docker-compose-developer.yml
DOCKER_COMPOSE_DEV_LABEL = com.grafana.oncall.env=dev

# compose profiles
MYSQL_PROFILE = mysql
POSTGRES_PROFILE = postgres
SQLITE_PROFILE = sqlite
ENGINE_PROFILE = engine
UI_PROFILE = oncall_ui
REDIS_PROFILE = redis
RABBITMQ_PROFILE = rabbitmq
GRAFANA_PROFILE = grafana

DEV_ENV_DIR = ./dev
DEV_ENV_FILE = $(DEV_ENV_DIR)/.env.dev
DEV_ENV_EXAMPLE_FILE = $(DEV_ENV_FILE).example

ENGINE_DIR = ./engine
REQUIREMENTS_TXT = $(ENGINE_DIR)/requirements.txt
REQUIREMENTS_ENTERPRISE_TXT = $(ENGINE_DIR)/requirements-enterprise.txt
SQLITE_DB_FILE = $(ENGINE_DIR)/oncall.db

# -n flag only copies DEV_ENV_EXAMPLE_FILE-> DEV_ENV_FILE if it doesn't already exist
$(shell cp -n $(DEV_ENV_EXAMPLE_FILE) $(DEV_ENV_FILE))
include $(DEV_ENV_FILE)

# if COMPOSE_PROFILES is set in DEV_ENV_FILE use it
# otherwise use a default (or what is passed in as an arg)
ifeq ($(COMPOSE_PROFILES),)
	COMPOSE_PROFILES=$(ENGINE_PROFILE),$(UI_PROFILE),$(REDIS_PROFILE),$(GRAFANA_PROFILE)
endif

# conditionally assign DB based on what is present in COMPOSE_PROFILES
ifeq ($(findstring $(MYSQL_PROFILE),$(COMPOSE_PROFILES)),$(MYSQL_PROFILE))
	DB=$(MYSQL_PROFILE)
else ifeq ($(findstring $(POSTGRES_PROFILE),$(COMPOSE_PROFILES)),$(POSTGRES_PROFILE))
	DB=$(POSTGRES_PROFILE)
else
	DB=$(SQLITE_PROFILE)
endif

# conditionally assign BROKER_TYPE based on what is present in COMPOSE_PROFILES
# if the user specifies both rabbitmq and redis, we'll make the assumption that rabbitmq is the broker
ifeq ($(findstring $(RABBITMQ_PROFILE),$(COMPOSE_PROFILES)),$(RABBITMQ_PROFILE))
	BROKER_TYPE=$(RABBITMQ_PROFILE)
else
	BROKER_TYPE=$(REDIS_PROFILE)
endif

# SQLITE_DB_FiLE is set to properly mount the sqlite db file
DOCKER_COMPOSE_ENV_VARS := COMPOSE_PROFILES=$(COMPOSE_PROFILES) DB=$(DB) BROKER_TYPE=$(BROKER_TYPE)
ifeq ($(DB),$(SQLITE_PROFILE))
	DOCKER_COMPOSE_ENV_VARS += SQLITE_DB_FILE=$(SQLITE_DB_FILE)
endif

define run_docker_compose_command
	$(DOCKER_COMPOSE_ENV_VARS) docker-compose -f $(DOCKER_COMPOSE_FILE) $(1)
endef

define run_engine_docker_command
	$(call run_docker_compose_command,run --rm oncall_engine_commands $(1))
endef

# touch SQLITE_DB_FILE if it does not exist and DB is eqaul to SQLITE_PROFILE
start:
ifeq ($(DB),$(SQLITE_PROFILE))
	@if [ ! -f $(SQLITE_DB_FILE) ]; then \
		touch $(SQLITE_DB_FILE); \
	fi
endif

	$(call run_docker_compose_command,up --remove-orphans -d)

init:
# if the oncall UI is to be run in docker we should do an initial build of the frontend code
# this makes sure that it will be available when the grafana container starts up without the need to
# restart the grafana container initially
ifeq ($(findstring $(UI_PROFILE),$(COMPOSE_PROFILES)),$(UI_PROFILE))
	cd grafana-plugin && yarn install && yarn build:dev
endif

stop:
	$(call run_docker_compose_command,down)

restart:
	$(call run_docker_compose_command,restart)

build:
	$(call run_docker_compose_command,build)

cleanup: stop
	docker system prune --filter label="$(DOCKER_COMPOSE_DEV_LABEL)" --all --volumes

install-pre-commit:
	@if [ ! -x "$$(command -v pre-commit)" ]; then \
		echo "installing pre-commit"; \
		pip install $$(grep "pre-commit" $(ENGINE_DIR)/requirements.txt); \
	else \
		echo "pre-commit already installed"; \
	fi

lint: install-pre-commit
	pre-commit run --all-files

install-precommit-hook: install-pre-commit
	pre-commit install

test:
	$(call run_engine_docker_command,pytest)

start-celery-beat:
	$(call run_engine_docker_command,celery -A engine beat -l info)

purge-queues:
	$(call run_engine_docker_command,celery -A engine purge -f)

shell:
	$(call run_engine_docker_command,python manage.py shell)

dbshell:
	$(call run_engine_docker_command,python manage.py dbshell)

engine-manage:
	$(call run_engine_docker_command,python manage.py $(CMD))

exec-engine:
	docker exec -it oncall_engine bash

_backend-debug-enable:
	$(shell ./dev/add_env_var.sh DEBUG True $(DEV_ENV_FILE))
	$(shell ./dev/add_env_var.sh SILK_PROFILER_ENABLED True $(DEV_ENV_FILE))

_backend-debug-disable:
	$(shell ./dev/add_env_var.sh DEBUG False $(DEV_ENV_FILE))
	$(shell ./dev/add_env_var.sh SILK_PROFILER_ENABLED False $(DEV_ENV_FILE))

backend-debug-enable: _backend-debug-enable stop start
backend-debug-disable: _backend-debug-disable stop start

# The below commands are useful for running backend services outside of docker
define backend_command
	export `grep -v '^#' $(DEV_ENV_FILE) | xargs -0` && \
	export BROKER_TYPE=$(BROKER_TYPE) && \
	cd engine && \
	$(1)
endef

backend-bootstrap:
	pip install -U pip wheel
	pip install -r $(REQUIREMENTS_TXT)
	@if [ -f $(REQUIREMENTS_ENTERPRISE_TXT) ]; then \
		pip install -r $(REQUIREMENTS_ENTERPRISE_TXT); \
	fi

backend-migrate:
	$(call backend_command,python manage.py migrate)

run-backend-server:
	$(call backend_command,python manage.py runserver 0.0.0.0:8080)

run-backend-celery:
	$(call backend_command,python manage.py start_celery)

backend-command:
	$(call backend_command,$(CMD))

backend-manage-command:
	$(call backend_command,python manage.py $(CMD))
