# Developer quickstart

- [Running the project](#running-the-project)
  - [`COMPOSE_PROFILES`](#compose_profiles)
  - [`GRAFANA_VERSION`](#grafana_version)
  - [Configuring Grafana](#configuring-grafana)
  - [Django Silk Profiling](#django-silk-profiling)
  - [Running backend services outside Docker](#running-backend-services-outside-docker)
- [UI Integration Tests](#ui-integration-tests)
- [Useful `make` commands](#useful-make-commands)
- [Setting environment variables](#setting-environment-variables)
- [Slack application setup](#slack-application-setup)
- [Update drone build](#update-drone-build)
- [Troubleshooting](#troubleshooting)
  - [ld: library not found for -lssl](#ld-library-not-found-for--lssl)
  - [Could not build wheels for cryptography which use PEP 517 and cannot be installed directly](#could-not-build-wheels-for-cryptography-which-use-pep-517-and-cannot-be-installed-directly)
  - [django.db.utils.OperationalError: (1366, "Incorrect string value")](#djangodbutilsoperationalerror-1366-incorrect-string-value)
  - [/bin/sh: line 0: cd: grafana-plugin: No such file or directory](#binsh-line-0-cd-grafana-plugin-no-such-file-or-directory)
  - [Encountered error while trying to install package - grpcio](#encountered-error-while-trying-to-install-package---grpcio)
  - [distutils.errors.CompileError: command '/usr/bin/clang' failed with exit code 1](#distutilserrorscompileerror-command-usrbinclang-failed-with-exit-code-1)
  - [symbol not found in flat namespace '\_EVP_DigestSignUpdate'](#symbol-not-found-in-flat-namespace-_evp_digestsignupdate)
- [IDE Specific Instructions](#ide-specific-instructions)
  - [PyCharm](#pycharm)
- [How to write database migrations](#how-to-write-database-migrations)

Related: [How to develop integrations](/engine/config_integrations/README.md)

## Running the project

By default everything runs inside Docker. These options can be modified via the [`COMPOSE_PROFILES`](#compose_profiles)
environment variable.

1. Firstly, ensure that you have `docker` [installed](https://docs.docker.com/get-docker/) and running on your machine.
   **NOTE**: the `docker-compose-developer.yml` file uses some syntax/features that are only supported by Docker Compose
   v2. For instructions on how to enable this (if you haven't already done so),
   see [here](https://www.docker.com/blog/announcing-compose-v2-general-availability/). Ensure you have Docker Compose
   version 2.10 or above installed - update instructions are [here](https://docs.docker.com/compose/install/linux/).
2. Run `make init start`. By default this will run everything in Docker, using SQLite as the database and Redis as the
   message broker/cache. See [`COMPOSE_PROFILES`](#compose_profiles) below for more details on how to swap
   out/disable which components are run in Docker.
3. Open Grafana in a browser [here](http://localhost:3000/plugins/grafana-oncall-app) (login: `oncall`, password: `oncall`).
4. You should now see the OnCall plugin configuration page. You may safely ignore the warning about the invalid
   plugin signature. When opening the main plugin page, you may also ignore warnings about version mismatch and lack of
   communication channels.
5. Enjoy! Check our [OSS docs](https://grafana.com/docs/grafana-cloud/oncall/open-source/) if you want to set up Slack,
   Telegram, Twilio or SMS/calls through Grafana Cloud.
6. (Optional) Install `pre-commit` hooks by running `make install-precommit-hook`

**Note**: on subsequent startups you can simply run `make start`, this is a bit faster because it skips the frontend
build step.

### `COMPOSE_PROFILES`

This configuration option represents a comma-separated list of [`docker-compose` profiles](https://docs.docker.com/compose/profiles/).
It allows you to swap-out, or disable, certain components in Docker.

This option can be configured in two ways:

1. Setting a `COMPOSE_PROFILES` environment variable in `dev/.env.dev`. This allows you to avoid having to set
   `COMPOSE_PROFILES` for each `make` command you execute afterwards.
2. Passing in a `COMPOSE_PROFILES` argument when running `make` commands. For example:

```bash
make start COMPOSE_PROFILES=postgres,engine,grafana,rabbitmq
```

The possible profiles values are:

- `grafana`
- `engine`
- `oncall_ui`
- `redis`
- `rabbitmq`
- `postgres`
- `mysql`

The default is `engine,oncall_ui,redis,grafana`. This runs:

- all OnCall components (using SQLite as the database)
- Redis as the Celery message broker/cache
- a Grafana container

### `GRAFANA_VERSION`

If you would like to change the version of Grafana being run, simply pass in a `GRAFANA_VERSION` environment variable
to `make start` (or alternatively set it in your `.env.dev` file). The value of this environment variable should be a
valid `grafana/grafana` published Docker [image tag](https://hub.docker.com/r/grafana/grafana/tags).

### Configuring Grafana

This section is applicable for when you are running a Grafana container inside of `docker-compose` and you would like
to modify your Grafana instance's provisioning configuration.

The following commands assume you run them from the root of the project:

```bash
touch ./dev/grafana.dev.ini
# make desired changes to ./dev/grafana.dev.ini then run
touch .env && ./dev/add_env_var.sh GRAFANA_DEV_PROVISIONING ./dev/grafana.dev.ini .env
```

The next time you start the project via `docker-compose`, the `grafana` container will have `./dev/grafana.dev.ini`
volume mounted inside the container.

### Django Silk Profiling

In order to setup [`django-silk`](https://github.com/jazzband/django-silk) for local profiling, perform the following
steps:

1. `make backend-debug-enable`
2. `make engine-manage CMD="createsuperuser"` - follow CLI prompts to create a Django superuser
3. Visit <http://localhost:8080/django-admin> and login using the credentials you created in step #2

You should now be able to visit <http://localhost:8080/silk/> and see the Django Silk UI.
See the `django-silk` documentation [here](https://github.com/jazzband/django-silk) for more information.

### Running backend services outside Docker

By default everything runs inside Docker. If you would like to run the backend services outside of Docker
(for integrating w/ PyCharm for example), follow these instructions:

1. Create a Python 3.9 virtual environment using a method of your choosing (ex.
   [venv](https://docs.python.org/3.9/library/venv.html) or [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)).
   Make sure the virtualenv is "activated".
2. `postgres` is a dependency on some of our Python dependencies (notably `psycopg2`
   ([docs](https://www.psycopg.org/docs/install.html#prerequisites))). Please visit
   [here](https://www.postgresql.org/download/) for installation instructions.
3. `make backend-bootstrap` - installs all backend dependencies
4. Modify your `.env.dev` by copying the contents of one of `.env.mysql.dev`, `.env.postgres.dev`,
   or `.env.sqlite.dev` into `.env.dev` (you should exclude the `GF_` prefixed environment variables).

   > In most cases where you are running stateful services via `docker-compose`, and backend services outside of
   > docker, you will simply need to change the database host to `localhost` (or in the case of `sqlite` update
   > the file-path to your `sqlite` database file). You will need to change the broker host to `localhost` as well.

5. `make backend-migrate` - runs necessary database migrations
6. Open two separate shells and then run the following:

- `make run-backend-server` - runs the HTTP server
- `make run-backend-celery` - runs Celery workers

## UI Integration Tests

We've developed a suite of "end-to-end" integration tests using [Playwright](https://playwright.dev/). These tests
are run on pull request CI builds. New features should ideally include a new/modified integration test.

To run these tests locally simply do the following:

```bash
npx playwright install  # install playwright dependencies
cp ./grafana-plugin/.env.example ./grafana-plugin/.env
# you may need to tweak the values in ./grafana-plugin/.env according to your local setup
yarn test:integration
```

## Useful `make` commands

See [`COMPOSE_PROFILES`](#compose_profiles) for more information on what this option is and how to configure it.

```bash
make init # build the frontend plugin code then run make start
make start # start all of the docker containers
make stop # stop all of the docker containers
make restart # restart all docker containers
make build # rebuild images (e.g. when changing requirements.txt)
# run Django's `manage.py` script, inside of a docker container, passing `$CMD` as arguments.
# e.g. `make engine-manage CMD="makemigrations"` - https://docs.djangoproject.com/en/4.1/ref/django-admin/#django-admin-makemigrations
make engine-manage CMD="..."

make backend-debug-enable # enable Django's debug mode and Silk profiling (this is disabled by default for performance reasons)
make backend-debug-disable # disable Django's debug mode and Silk profiling

# this will remove all of the images, containers, volumes, and networks
# associated with your local OnCall developer setup
make cleanup

make start-celery-beat # start celery beat
make purge-queues # purge celery queues
make shell # starts an OnCall engine Django shell
make dbshell # opens a DB shell
make exec-engine # exec into engine container's bash
make test # run backend tests

# run Django's `manage.py` script, passing `$CMD` as arguments.
# e.g. `make backend-manage-command CMD="makemigrations"` - https://docs.djangoproject.com/en/4.1/ref/django-admin/#django-admin-makemigrations
make backend-manage-command CMD="..."

# run both frontend and backend linters
# may need to run `yarn install` from within `grafana-plugin` to install several `pre-commit` dependencies
make lint
```

## Setting environment variables

If you need to override any additional environment variables, you should set these in a root `.env.dev` file.
This file is automatically picked up by the OnCall engine Docker containers. This file is ignored from source control
and also overrides any defaults that are set in other `.env*` files

## Slack application setup

For Slack app configuration check our docs: <https://grafana.com/docs/grafana-cloud/oncall/open-source/#slack-setup>

## Update drone build

The `.drone.yml` build file must be signed when changes are made to it. Follow these steps:

If you have not installed drone CLI follow [these instructions](https://docs.drone.io/cli/install/)

To sign the `.drone.yml` file:

```bash
export DRONE_SERVER=https://drone.grafana.net

# Get your drone token from https://drone.grafana.net/account
export DRONE_TOKEN=<Your DRONE_TOKEN>

drone sign --save grafana/oncall .drone.yml
```

## Troubleshooting

### ld: library not found for -lssl

**Problem:**

```bash
make backend-bootstrap
...
    ld: library not found for -lssl
    clang: error: linker command failed with exit code 1 (use -v to see invocation)
    error: command 'gcc' failed with exit status 1
...
```

**Solution:**

```bash
export LDFLAGS=-L/usr/local/opt/openssl/lib
make backend-bootstrap
```

### Could not build wheels for cryptography which use PEP 517 and cannot be installed directly

Happens on Apple Silicon

**Problem:**

```bash
build/temp.macosx-12-arm64-3.9/_openssl.c:575:10: fatal error: 'openssl/opensslv.h' file not found
#include <openssl/opensslv.h>
          ^~~~~~~~~~~~~~~~~~~~
1 error generated.
error: command '/usr/bin/clang' failed with exit code 1
----------------------------------------
ERROR: Failed building wheel for cryptography
```

**Solution:**

<!-- markdownlint-disable MD013 -->

```bash
LDFLAGS="-L$(brew --prefix openssl@1.1)/lib" CFLAGS="-I$(brew --prefix openssl@1.1)/include" pip install `cat engine/requirements.txt | grep cryptography`
```

<!-- markdownlint-enable MD013 -->

### django.db.utils.OperationalError: (1366, "Incorrect string value")

**Problem:**

<!-- markdownlint-disable MD013 -->

```bash
django.db.utils.OperationalError: (1366, "Incorrect string value: '\\xF0\\x9F\\x98\\x8A\\xF0\\x9F...' for column 'cached_name' at row 1")
```

<!-- markdownlint-enable MD013 -->

**Solution:**

Recreate the database with the correct encoding.

### /bin/sh: line 0: cd: grafana-plugin: No such file or directory

**Problem:**

When running `make init`:

```bash
/bin/sh: line 0: cd: grafana-plugin: No such file or directory
make: *** [init] Error 1
```

This arises when the environment variable `[CDPATH](https://www.theunixschool.com/2012/04/what-is-cdpath.html)` is
set _and_ when the current path (`.`) is not explicitly part of `CDPATH`.

**Solution:**

Either make `.` part of `CDPATH` in your .rc file setup, or temporarily override the variable when running `make` commands:

```bash
$ CDPATH="." make init
# Setting CDPATH to empty seems to also work - only tested on zsh, YMMV
$ CDPATH="" make init
```

**Problem:**

When running `make init start`:

<!-- markdownlint-disable MD013 -->

```bash
Error response from daemon: open /var/lib/docker/overlay2/ac57b871108ee1b98ff4455e36d2175eae90cbc7d4c9a54608c0b45cfb7c6da5/committed: is a directory
make: *** [start] Error 1
```

<!-- markdownlint-enable MD013 -->

**Solution:**
clear everything in docker by resetting or:

```bash
make cleanup
```

### Encountered error while trying to install package - grpcio

**Problem:**

We are currently using a library, `fcm-django`, which has a dependency on `grpcio`. Google does not provide `grpcio`
wheels built for Apple Silicon Macs. The best solution so far has been to use a `conda` virtualenv. There's apparently
a lot of community work put into making packages play well with M1/arm64 architecture.

```bash
pip install -r requirements.txt
...
   note: This error originates from a subprocess, and is likely not a problem with pip.
error: legacy-install-failure

× Encountered error while trying to install package.
╰─> grpcio
...
```

**Solution:**

Use a `conda` virtualenv, and then run the following when installing the engine dependencies/
[See here for more details](https://stackoverflow.com/a/74307636/3902555)

```bash
GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=1 GRPC_PYTHON_BUILD_SYSTEM_ZLIB=1 pip install -r requirements.txt
```

### distutils.errors.CompileError: command '/usr/bin/clang' failed with exit code 1

See solution for "Encountered error while trying to install package - grpcio" [here](#encountered-error-while-trying-to-install-package---grpcio)

### symbol not found in flat namespace '\_EVP_DigestSignUpdate'

**Problem:**

This problem seems to occur when running the Celery process, outside of `docker-compose`
(via `make run-backend-celery`), and using a `conda` virtual environment.

<!-- markdownlint-disable MD013 -->

```bash
conda create --name oncall-dev python=3.9.13
conda activate oncall-dev
make backend-bootstrap
make run-backend-celery
File "~/oncall/engine/engine/__init__.py", line 5, in <module>
    from .celery import app as celery_app
  File "~/oncall/engine/engine/celery.py", line 11, in <module>
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
  File "/opt/homebrew/Caskroom/miniconda/base/envs/oncall-dev/lib/python3.9/site-packages/opentelemetry/exporter/otlp/proto/grpc/trace_exporter/__init__.py", line 20, in <module>
    from grpc import ChannelCredentials, Compression
  File "/opt/homebrew/Caskroom/miniconda/base/envs/oncall-dev/lib/python3.9/site-packages/grpc/__init__.py", line 22, in <module>
    from grpc import _compression
  File "/opt/homebrew/Caskroom/miniconda/base/envs/oncall-dev/lib/python3.9/site-packages/grpc/_compression.py", line 20, in <module>
    from grpc._cython import cygrpc
ImportError: dlopen(/opt/homebrew/Caskroom/miniconda/base/envs/oncall-dev/lib/python3.9/site-packages/grpc/_cython/cygrpc.cpython-39-darwin.so, 0x0002): symbol not found in flat namespace '_EVP_DigestSignUpdate'
```

<!-- markdownlint-enable MD013 -->

**Solution:**

[This solution](https://github.com/grpc/grpc/issues/15510#issuecomment-392012594) posted in a GitHub issue thread for
the `grpc/grpc` repository, fixes the issue:

```bash
conda install grpcio
make run-backend-celery
```

## IDE Specific Instructions

### PyCharm

1. Follow the instructions listed in ["Running backend services outside Docker"](#running-backend-services-outside-docker).
2. Open the project in PyCharm
3. Settings &rarr; Project OnCall
   - In Python Interpreter click the gear and create a new Virtualenv from existing environment selecting the
     venv created in Step 1.
   - In Project Structure make sure the project root is the content root and add /engine to Sources
4. Under Settings &rarr; Languages & Frameworks &rarr; Django
   - Enable Django support
   - Set Django project root to /engine
   - Set Settings to settings/dev.py
5. Create a new Django Server run configuration to Run/Debug the engine
   - Use a plugin such as EnvFile to load the .env.dev file
   - Change port from 8000 to 8080

## How to write database migrations

We use [django-migration-linter](https://github.com/3YOURMIND/django-migration-linter) to keep database migrations
backwards compatible

- we can automatically run migrations and they are zero-downtime, e.g. old code can work with the migrated database
- we can run and rollback migrations without worrying about data safety
- OnCall is deployed to the multiple environments core team is not able to control

See [django-migration-linter checklist](https://github.com/3YOURMIND/django-migration-linter/blob/main/docs/incompatibilities.md)
for the common mistakes and best practices
