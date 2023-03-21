help:
	@sed \
		-e '/^[a-zA-Z0-9_\-]*:.*##/!d' \
		-e 's/:.*##\s*/:/' \
		-e 's/^\(.\+\):\(.*\)/$(shell tput setaf 6)\1$(shell tput sgr0):\2/' \
		$(MAKEFILE_LIST) | column -c2 -t -s :

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
	$(DOCKER_COMPOSE_ENV_VARS) docker compose -f $(DOCKER_COMPOSE_FILE) $(1)
endef

define run_engine_docker_command
	$(call run_docker_compose_command,run --rm oncall_engine_commands $(1))
endef

# touch SQLITE_DB_FILE if it does not exist and DB is eqaul to SQLITE_PROFILE
start:  ## start all of the docker containers
ifeq ($(DB),$(SQLITE_PROFILE))
	@if [ ! -f $(SQLITE_DB_FILE) ]; then \
		touch $(SQLITE_DB_FILE); \
	fi
endif

	$(call run_docker_compose_command,up --remove-orphans -d)

init:  ## build the frontend plugin code then run make start
# if the oncall UI is to be run in docker we should do an initial build of the frontend code
# this makes sure that it will be available when the grafana container starts up without the need to
# restart the grafana container initially
ifeq ($(findstring $(UI_PROFILE),$(COMPOSE_PROFILES)),$(UI_PROFILE))
	cd grafana-plugin && yarn install && yarn build:dev
endif

stop:  # stop all of the docker containers
	$(call run_docker_compose_command,down)

restart:  ## restart all docker containers
	$(call run_docker_compose_command,restart)

build:  ## rebuild images (e.g. when changing requirements.txt)
	$(call run_docker_compose_command,build)

cleanup: stop  ## this will remove all of the images, containers, volumes, and networks
               ## associated with your local OnCall developer setup
	docker system prune --filter label="$(DOCKER_COMPOSE_DEV_LABEL)" --all --volumes

install-pre-commit:
	@if [ ! -x "$$(command -v pre-commit)" ]; then \
		echo "installing pre-commit"; \
		pip install $$(grep "pre-commit" $(ENGINE_DIR)/requirements.txt); \
	else \
		echo "pre-commit already installed"; \
	fi

lint: install-pre-commit  ## run both frontend and backend linters
                          ## may need to run `yarn install` from within `grafana-plugin`
                          ## to install several `pre-commit` dependencies

	pre-commit run --all-files

install-precommit-hook: install-pre-commit
	pre-commit install

test:  ## run backend tests
	$(call run_engine_docker_command,pytest)

start-celery-beat:  ## start celery beat
	$(call run_engine_docker_command,celery -A engine beat -l info)

purge-queues: ## purge celery queues
	$(call run_engine_docker_command,celery -A engine purge -f)

shell:  ## starts an OnCall engine Django shell
	$(call run_engine_docker_command,python manage.py shell)

dbshell:  ## opens a DB shell
	$(call run_engine_docker_command,python manage.py dbshell)

engine-manage:  ## run Django's `manage.py` script, inside of a docker container, passing `$CMD` as arguments.
                ## e.g. `make engine-manage CMD="makemigrations"`
                ## https://docs.djangoproject.com/en/4.1/ref/django-admin/#django-admin-makemigrations
	$(call run_engine_docker_command,python manage.py $(CMD))

exec-engine:  ## exec into engine container's bash
	docker exec -it oncall_engine bash

_backend-debug-enable:  ## enable Django's debug mode and Silk profiling (this is disabled by default for performance reasons)
	$(shell ./dev/add_env_var.sh DEBUG True $(DEV_ENV_FILE))
	$(shell ./dev/add_env_var.sh SILK_PROFILER_ENABLED True $(DEV_ENV_FILE))

_backend-debug-disable:  ## disable Django's debug mode and Silk profiling
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

backend-manage-command:  ## run Django's `manage.py` script, passing `$CMD` as arguments.
                         ## e.g. `make backend-manage-command CMD="makemigrations"`
                         ## https://docs.djangoproject.com/en/4.1/ref/django-admin/#django-admin-makemigrations
                         ## alternatively you can open docker container with engine and run commands from there
	$(call backend_command,python manage.py $(CMD))
