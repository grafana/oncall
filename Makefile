help:
	@sed \
		-e '/^[a-zA-Z0-9_\-\/\-]*:.*##/!d' \
		-e 's/:.*##\s*/:/' \
		-e 's/^\(.\+\):\(.*\)/$(shell tput setaf 6)\1$(shell tput sgr0):\2/' \
		$(MAKEFILE_LIST) | column -c2 -t -s :

ENGINE_DIR = ./engine
DEV_ENV_DIR = ./dev
DEV_ENV_FILE = $(DEV_ENV_DIR)/.env.dev
DEV_HELM_USER_SPECIFIC_FILE = $(DEV_ENV_DIR)/helm-local.dev.yml

# make sure that DEV_HELM_USER_SPECIFIC_FILE exists
# (NOTE: touch will only create the file if it doesn't already exist)
$(shell touch $(DEV_HELM_USER_SPECIFIC_FILE))

# switch the k8s context to always run commands against the local kind cluster
# the "kubectl get pods" + grep command essentially finds the pod name of the currently running engine pod
# grep -v will make sure we are not grabbing the oncall-engine-migrate pod
#
# need the -o flag to xargs otherwise we can't open a TTY to the pod
# https://github.com/kubernetes/kubernetes/issues/37471#issuecomment-378738512
define run_engine_k8s_command
	kubectl config use-context kind-kind
	kubectl get pods --no-headers -o custom-columns=":metadata.name" --selector="app.kubernetes.io/component=engine" | grep -v 'migrate' | xargs -o -I{} kubectl exec -it {} -- $(1)
endef

# always use settings.ci-test django settings file when running the tests
# if we use settings.dev it's very possible that some fail just based on the settings alone
define run_backend_tests
	$(call run_engine_k8s_command,pytest --ds=settings.ci-test $(1))
endef

.PHONY: local/up
local/up: cluster/up  ## deploy all containers locally via tilt (k8s cluster will be created if it doesn't exist)
	tilt up

.PHONY: local/down
local/down:  ## remove all containers deployed via tilt
	tilt down

.PHONY: local/clean
local/clean: cluster/down ## clean up k8s local dev environment

.PHONY: cluster/up
cluster/up:  ## create a local development k8s cluster
	ctlptl apply -f dev/kind-config.yaml

.PHONY: cluster/down
cluster/down: ## delete local development k8s cluster
	ctlptl delete -f dev/kind-config.yaml

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

purge-queues: ## purge celery queues
	$(call run_engine_k8s_command,celery -A engine purge -f)

shell:  ## starts an OnCall engine Django shell
	$(call run_engine_k8s_command,python manage.py shell)

dbshell:  ## opens a DB shell
	$(call run_engine_k8s_command,python manage.py dbshell)

engine-manage:  ## run Django's `manage.py` script, inside of a docker container, passing `$CMD` as arguments.
                ## e.g. `make engine-manage CMD="makemigrations"`
                ## https://docs.djangoproject.com/en/4.1/ref/django-admin/#django-admin-makemigrations
	$(call run_engine_k8s_command,python manage.py $(CMD))

exec-engine:  ## exec into engine container's bash
	$(call run_engine_k8s_command,sh)

test-e2e:  ## run the e2e tests in headless mode
	yarn --cwd grafana-plugin test:e2e

test-e2e-watch:  ## start e2e tests in watch mode
	yarn --cwd grafana-plugin test:e2e:watch

test-e2e-show-report:  ## open last e2e test report
	yarn --cwd grafana-plugin playwright show-report

ui-test:  ## run the UI tests
	yarn --cwd grafana-plugin test

ui-lint:  ## run the UI linter
	yarn --cwd grafana-plugin lint

ui-build:  ## build the UI
	yarn --cwd grafana-plugin build

test-helm:  ## run helm unit tests
	helm unittest ./helm/oncall $(ARGS)

backend-debug-enable:  ## enable Django's debug mode and Silk profiling (this is disabled by default for performance reasons)
	$(shell ./dev/add_env_var.sh DEBUG True $(DEV_ENV_FILE))
	$(shell ./dev/add_env_var.sh SILK_PROFILER_ENABLED True $(DEV_ENV_FILE))

backend-debug-disable:  ## disable Django's debug mode and Silk profiling
	$(shell ./dev/add_env_var.sh DEBUG False $(DEV_ENV_FILE))
	$(shell ./dev/add_env_var.sh SILK_PROFILER_ENABLED False $(DEV_ENV_FILE))
