DOCKER_COMPOSE_FILE=docker-compose-developer.yml
DOCKER_COMPOSE_DEV_LABEL=com.grafana.oncall.env=dev

# -n flag only copies .env.dev.example -> .env.dev if it doesn't already exist
$(shell cp -n ./dev/.env.dev.example ./dev/.env.dev)
include ./dev/.env.dev

# if COMPOSE_PROFILES is set in ./dev/.env.dev use it
# otherwise use a default (or what is passed in as an arg)
ifeq ($(COMPOSE_PROFILES),)
	COMPOSE_PROFILES=engine,oncall_ui,redis,grafana
endif

# conditionally assign DB based on what is present in COMPOSE_PROFILES
ifeq ($(findstring mysql,$(COMPOSE_PROFILES)),mysql)
	DB=mysql
else ifeq ($(findstring mysql,$(COMPOSE_PROFILES)),mysql)
	DB=postgres
else
	DB=sqlite
endif

# conditionally assign BROKER_TYPE based on what is present in COMPOSE_PROFILES
# if the user specifies both rabbitmq and redis, we'll make the assumption that rabbitmq is the broker
ifeq ($(findstring rabbitmq,$(COMPOSE_PROFILES)),rabbitmq)
	BROKER_TYPE=rabbitmq
else
	BROKER_TYPE=redis
endif

define run_engine_docker_command
    DB=$(DB) BROKER_TYPE=$(BROKER_TYPE) docker-compose -f $(DOCKER_COMPOSE_FILE) run --rm oncall_engine_commands $(1)
endef

define run_docker_compose_command
	COMPOSE_PROFILES=$(COMPOSE_PROFILES) DB=$(DB) BROKER_TYPE=$(BROKER_TYPE) docker-compose -f $(DOCKER_COMPOSE_FILE) $(1)
endef

# touch ./engine/oncall.db if it does not exist and DB is eqaul to sqlite
# conditionally set BROKER_TYPE env var that is passed to docker-compose, based on COMPOSE_PROFILES make arg
# start docker-compose
start:
ifeq ($(DB),sqlite)
	@if [ ! -f ./engine/oncall.db ]; then \
		touch ./engine/oncall.db; \
	fi
endif

	$(call run_docker_compose_command,up --remove-orphans -d)

stop:
	$(call run_docker_compose_command,down)

restart:
	$(call run_docker_compose_command,restart)

cleanup:
	docker system prune --filter label="$(DOCKER_COMPOSE_DEV_LABEL)" --all --volumes

install-pre-commit:
	@if [ ! -x "$$(command -v pre-commit)" ]; then \
		echo "installing pre-commit"; \
		pip install $$(grep "pre-commit" engine/requirements.txt); \
	else \
		echo "pre-commit already installed"; \
	fi

lint: install-pre-commit
	pre-commit run --all-files

install-precommit-hook: install-pre-commit
	pre-commit install

get-invite-token:
	$(call run_engine_docker_command,python manage.py issue_invite_for_the_frontend --override)

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
