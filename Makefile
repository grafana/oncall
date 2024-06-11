help:
	@sed \
		-e '/^[a-zA-Z0-9_\-\/\-]*:.*##/!d' \
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
PROMETHEUS_PROFILE = prometheus
GRAFANA_PROFILE = grafana
TELEGRAM_POLLING_PROFILE = telegram_polling

DEV_ENV_DIR = ./dev
DEV_ENV_FILE = $(DEV_ENV_DIR)/.env.dev
DEV_ENV_EXAMPLE_FILE = $(DEV_ENV_FILE).example

DEV_HELM_FILE = $(DEV_ENV_DIR)/helm-local.yml
DEV_HELM_USER_SPECIFIC_FILE = $(DEV_ENV_DIR)/helm-local.dev.yml

ENGINE_DIR = ./engine
VENV_DIR = ./venv
REQUIREMENTS_DEV_IN = $(ENGINE_DIR)/requirements-dev.in
REQUIREMENTS_DEV_TXT = $(ENGINE_DIR)/requirements-dev.txt
REQUIREMENTS_IN = $(ENGINE_DIR)/requirements.in
REQUIREMENTS_TXT = $(ENGINE_DIR)/requirements.txt
REQUIREMENTS_ENTERPRISE_TXT = $(ENGINE_DIR)/requirements-enterprise.txt
SQLITE_DB_FILE = $(ENGINE_DIR)/oncall.db

# make sure that DEV_HELM_USER_SPECIFIC_FILE and SQLITE_DB_FILE always exists
# (NOTE: touch will only create the file if it doesn't already exist)
$(shell touch $(DEV_HELM_USER_SPECIFIC_FILE))
$(shell touch $(SQLITE_DB_FILE))

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

# TODO: remove this when docker-compose local setup is removed
# https://stackoverflow.com/a/649462
define _DEPRECATION_MESSAGE
⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️
NOTE: docker-compose based make commands will be deprecated on (or around) October 1, 2023, in favour of
tilt/k8s based commands. Please familirize yourself with the tilt/k8s commands.

See https://github.com/grafana/oncall/tree/dev/dev for instructions on how to use tilt helm/k8s commands.
⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️


endef
export _DEPRECATION_MESSAGE
define echo_deprecation_message
	@echo "$$_DEPRECATION_MESSAGE"
endef

# SQLITE_DB_FiLE is set to properly mount the sqlite db file
DOCKER_COMPOSE_ENV_VARS := COMPOSE_PROFILES=$(COMPOSE_PROFILES) DB=$(DB) BROKER_TYPE=$(BROKER_TYPE)

# It's better to output pip log on the fly while building because it takes a lot of time
DOCKER_COMPOSE_ENV_VARS += BUILDKIT_PROGRESS=plain

ifeq ($(DB),$(SQLITE_PROFILE))
	DOCKER_COMPOSE_ENV_VARS += SQLITE_DB_FILE=$(SQLITE_DB_FILE)
endif

define run_docker_compose_command
	$(call echo_deprecation_message)
	$(DOCKER_COMPOSE_ENV_VARS) docker compose -f $(DOCKER_COMPOSE_FILE) $(1)
endef

define run_engine_docker_command
	$(call run_docker_compose_command,run --rm oncall_engine_commands $(1))
endef

define run_ui_docker_command
	$(call run_docker_compose_command,run --rm oncall_ui sh -c '$(1)')
endef

# always use settings.ci_test django settings file when running the tests
# if we use settings.dev it's very possible that some fail just based on the settings alone
define run_backend_tests
	$(call run_engine_docker_command,pytest --ds=settings.ci_test $(1))
endef

.PHONY: local/up
local/up: cluster/up  ## (beta) deploy all containers locally via tilt (k8s cluster will be created if it doesn't exist)
	tilt up

.PHONY: local/down
local/down:  ## (beta) remove all containers deployed via tilt
	tilt down

.PHONY: local/clean
local/clean: cluster/down ## (beta) clean up k8s local dev environment

.PHONY: cluster/up
cluster/up:  ## (beta) create a local development k8s cluster
	ctlptl apply -f dev/kind-config.yaml

.PHONY: cluster/down
cluster/down: ## (beta) delete local development k8s cluster
	ctlptl delete -f dev/kind-config.yaml

start:  ## start all of the docker containers
	$(call run_docker_compose_command,up --remove-orphans -d)

init:  ## build the frontend plugin code then run make start
# if the oncall UI is to be run in docker we should do an initial build of the frontend code
# this makes sure that it will be available when the grafana container starts up without the need to
# restart the grafana container initially
ifeq ($(findstring $(UI_PROFILE),$(COMPOSE_PROFILES)),$(UI_PROFILE))
	$(call run_ui_docker_command,yarn install && yarn build:dev)
endif

stop:  # stop all of the docker containers
	$(call run_docker_compose_command,down)

restart:  ## restart all docker containers
	$(call run_docker_compose_command,restart)

build:  ## rebuild images (e.g. when changing requirements.txt)
	$(call run_docker_compose_command,build)

cleanup: stop  ## this will remove all of the images, containers, volumes, and networks
               ## associated with your local OnCall developer setup
	$(call echo_deprecation_message)
	docker system prune --filter label="$(DOCKER_COMPOSE_DEV_LABEL)" --all --volumes

install-pre-commit:
	@if [ ! -x "$$(command -v pre-commit)" ]; then \
		echo "installing pre-commit"; \
		pip install $$(grep "pre-commit" $(ENGINE_DIR)/requirements-dev.txt); \
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
	$(call run_backend_tests)

test-dev:  ## very similar to `test` command, but allows you to pass arbitray args to pytest
           ## for example, `make test-dev ARGS="--last-failed --pdb"
	$(call run_backend_tests,$(ARGS))

test-helm:  ## run helm unit tests
	helm unittest ./helm/oncall $(ARGS)

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

test-e2e:  ## run the e2e tests in headless mode
	yarn --cwd grafana-plugin test:e2e

test-e2e-watch:  ## start e2e tests in watch mode
	yarn --cwd grafana-plugin test:e2e:watch

test-e2e-show-report:  ## open last e2e test report
	yarn --cwd grafana-plugin playwright show-report

ui-test:  ## run the UI tests
	$(call run_ui_docker_command,yarn test)

ui-lint:  ## run the UI linter
	$(call run_ui_docker_command,yarn lint)

ui-build:  ## build the UI
	$(call run_ui_docker_command,yarn build)

ui-command:  ## run any command, inside of a UI docker container, passing `$CMD` as arguments.
             ## e.g. `make ui-command CMD="yarn test"`
	$(call run_ui_docker_command,$(CMD))

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

pip-compile-locked-dependencies:  ## compile engine requirements.txt files
	$(shell cd engine && uv pip compile requirements.in -o requirements.txt)
	$(shell cd engine && uv pip compile requirements-dev.in -o requirements-dev.txt)

# The below commands are useful for running backend services outside of docker
define backend_command
	export `grep -v '^#' $(DEV_ENV_FILE) | xargs -0` && \
	export BROKER_TYPE=$(BROKER_TYPE) && \
	. ./venv/bin/activate && \
	cd engine && \
	$(1)
endef

backend-bootstrap:
	python3.12 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install -U pip wheel uv
	$(VENV_DIR)/bin/uv pip sync $(REQUIREMENTS_TXT) $(REQUIREMENTS_DEV_TXT)
	@if [ -f $(REQUIREMENTS_ENTERPRISE_TXT) ]; then \
		$(VENV_DIR)/bin/uv pip install -r $(REQUIREMENTS_ENTERPRISE_TXT); \
	fi

backend-migrate:
	$(call backend_command,python manage.py migrate)

backend-compile-deps:
	uv pip compile --strip-extras $(REQUIREMENTS_IN)
	uv pip compile --strip-extras $(REQUIREMENTS_DEV_IN)

backend-upgrade-deps:
	uv pip compile --strip-extras --upgrade $(REQUIREMENTS_IN)

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
