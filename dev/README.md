# Developer quickstart

Related: [How to develop integrations](/engine/config_integrations/README.md)

## Quick Start using Kubernetes and Tilt (beta)

> If you are experiencing issues, please check "Running the project with docker-compose".

### Install dependencies

- [Tilt | Kubernetes for Prod, Tilt for Dev](https://tilt.dev/)
- [tilt-dev/ctlptl: Making local Kubernetes clusters fun and easy to set up](https://github.com/tilt-dev/ctlptl)
- [Kind](https://kind.sigs.k8s.io)
- [Yarn](https://classic.yarnpkg.com/lang/en/docs/install/#mac-stable)

### Launch the environment

1. Create local k8s cluster:

   ```bash
   make cluster/up
   ```

2. Deploy the project:

   ```bash
   tilt up
   ```

   You can set local environment variables using `dev/helm-local.dev.yml` file, e.g.:

   ```yaml
   env:
     - name: FEATURE_LABELS_ENABLED_FOR_ALL
       value: "True"
   ```

3. Wait until all resources are green and open <http://localhost:3000/a/grafana-oncall-app> (user: oncall, password: oncall)

4. Modify source code, backend and frontend will be hot reloaded

5. Clean up the project by deleting the local k8s cluster:

   ```bash
   make cluster/down
   ```

## Running the project with docker-compose

By default everything runs inside Docker. These options can be modified via the [`COMPOSE_PROFILES`](#compose_profiles)
environment variable.

1. Firstly, ensure that you have `docker` [installed](https://docs.docker.com/get-docker/) and running on your machine.
   **NOTE**: the `docker-compose-developer.yml` file uses some syntax/features that are only supported by Docker Compose
   v2. For instructions on how to enable this (if you haven't already done so),
   see [here](https://www.docker.com/blog/announcing-compose-v2-general-availability/). Ensure you have Docker Compose
   version 2.20.2 or above installed - update instructions are [here](https://docs.docker.com/compose/install/linux/).
2. Run `make init start`. By default this will run everything in Docker, using SQLite as the database and Redis as the
   message broker/cache. See [`COMPOSE_PROFILES`](#compose_profiles) below for more details on how to swap
   out/disable which components are run in Docker.
3. Open Grafana in a browser [here](http://localhost:3000/plugins/grafana-oncall-app) (login: `oncall`, password: `oncall`).
4. You should now see the OnCall plugin configuration page. You may safely ignore the warning about the invalid
   plugin signature. Set "OnCall backend URL" as "http://host.docker.internal:8080". When opening the main plugin page,
   you may also ignore warnings about version mismatch and lack of communication channels.
5. Enjoy! Check our [OSS docs](https://grafana.com/docs/oncall/latest/open-source/) if you want to set up Slack,
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
- `prometheus`
- `engine`
- `oncall_ui`
- `redis`
- `rabbitmq`
- `postgres`
- `mysql`
- `telegram_polling`

The default is `engine,oncall_ui,redis,grafana`. This runs:

- all OnCall components (using SQLite as the database)
- Redis as the Celery message broker/cache
- a Grafana container

### `GRAFANA_IMAGE`

If you would like to change the image or version of Grafana being run, simply pass in a `GRAFANA_IMAGE` environment variable
to `make start` (or alternatively set it in your root `.env` file). The value of this environment variable should be a
valid `grafana` image/tag combination (ex. `grafana:main` or `grafana-enterprise:latest`).

### Configuring Grafana

This section is applicable for when you are running a Grafana container inside of `docker-compose` and you would like
to modify your Grafana instance's provisioning configuration.

The following commands assume you run them from the root of the project:

```bash
touch ./dev/grafana.dev.ini
# make desired changes to ./dev/grafana.dev.ini then run
touch .env && ./dev/add_env_var.sh GRAFANA_DEV_PROVISIONING ./dev/grafana/grafana.dev.ini .env
```

For example, if you would like to enable the `topnav` feature toggle, you can modify your `./dev/grafana.dev.ini` as
such:

```ini
[feature_toggles]
enable = top_nav
```

The next time you start the project via `docker-compose`, the `grafana` container will have `./dev/grafana/grafana.dev.ini`
volume mounted inside the container.

#### Modifying Provisioning Configuration

Files under `./dev/grafana/provisioning` are volume mounted into your Grafana container and allow you to easily
modify the instance's provisioning configuration. See the Grafana docs [here](https://grafana.com/docs/grafana/latest/administration/provisioning/#:~:text=You%20can%20manage%20data%20sources,match%20the%20provisioned%20configuration%20file.)
for more information.

### Enabling RBAC for OnCall for local development

To run the project locally w/ RBAC for OnCall enabled, you will first need to run a `grafana-enterprise` container,
instead of a `grafana` container. See the instructions [here](#grafana_image) on how to do so.

Next, you will need to follow the steps [here](https://grafana.com/docs/grafana/latest/administration/enterprise-licensing/)
on setting up/downloading a Grafana Enterprise license.

Lastly, you will need to modify the instance's configuration. Follow the instructions [here](#configuring-grafana) on
how to do so. You can modify your configuration file (`./dev/grafana.dev.ini`) as such:

```ini
[rbac]
enabled = true

[feature_toggles]
enable = accessControlOnCall

[server]
root_url = https://<your-stack-slug>.grafana.net/

[enterprise]
license_text = <content-of-the-license-jwt-that-you-downloaded>
```

(_Note_: you may need to restart your `grafana` container after modifying its configuration)

### Enabling OnCall prometheus exporter for local development

Add `prometheus` to your `COMPOSE_PROFILES` and set `FEATURE_PROMETHEUS_EXPORTER_ENABLED=True` in your
`dev/.env.dev` file. You may need to restart your `grafana` container to make sure the new datasource
is added (or add it manually using the UI; Prometheus will be running in `host.docker.internal:9090`
by default, using default settings).

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

1. Make sure you have Python 3.11 installed.
2. `postgres` is a dependency on some of our Python dependencies (notably `psycopg2`
   ([docs](https://www.psycopg.org/docs/install.html#prerequisites))). Please visit
   [here](https://www.postgresql.org/download/) for installation instructions.
3. `make backend-bootstrap` - will create the virtual env and install all backend dependencies
4. Modify your `.env.dev` by copying the contents of one of `.env.mysql.dev`, `.env.postgres.dev`,
   or `.env.sqlite.dev` into `.env.dev` (you should exclude the `GF_` prefixed environment variables).

   > In most cases where you are running stateful services via `docker-compose`, and backend services outside of
   > docker, you will simply need to change the database host to `localhost` (or in the case of `sqlite` update
   > the file-path to your `sqlite` database file). You will need to change the broker host to `localhost` as well.

5. `make backend-migrate` - runs necessary database migrations
6. Open two separate shells and then run the following:

- `make run-backend-server` - runs the HTTP server
- `make run-backend-celery` - runs Celery workers

### Adding or updating Python dependencies

We are using [pip-tools](https://github.com/jazzband/pip-tools) to manage our dependencies. It helps
making builds deterministic, controlling deps (and indirect deps) upgrades (and versions consistency)
avoiding unexpected (and potentially breaking) changes.

We keep our direct deps in `requirements.in` from which we generate (through `pip-compile`) the
`requirements.txt` (where all deps are pinned). We also constrain dev (and enterprise) deps based
on our base requirements. Check [how to update deps](https://github.com/jazzband/pip-tools?tab=readme-ov-file#updating-requirements).

`pip install -r requirements.txt` will keep working (the difference is that this should never
bring additional dependencies or different versions not listed there), and when starting an env
from scratch, it would be the same as running `pip-sync`. `pip-sync` on the other hand will also
ensure to clean up any deps not listed in the requirements, keeping the env exactly as described
in `requirements.txt`.

## UI E2E Tests

We've developed a suite of "end-to-end" integration tests using [Playwright](https://playwright.dev/). These tests
are run on pull request CI builds. New features should ideally include a new/modified integration test.

To run these tests locally simply do the following:

1. Install Playwright dependencies with `npx playwright install`
2. [Launch the environment](#launch-the-environment)
3. Then you interact with tests in 2 different ways:
   1. Using `Tilt` - open _E2eTests_ section where you will find 4 buttons:
      1. Restart headless run (you can configure browsers, reporter and failure allowance there)
      2. Open watch mode
      3. Show last HTML report
      4. Stop (stops any pending e2e test process)
   2. Using `make`:
      1. `make test:e2e` to start headless run
      2. `make test:e2e:watch` to open watch mode
      3. `make test:e2e:show:report` to open last HTML report

## Helm unit tests

To run the `helm` unit tests you will need the following dependencies installed:

- `helm` - [installation instructions](https://helm.sh/docs/intro/install/)
- `helm-unittest` plugin - [installation instructions](https://github.com/helm-unittest/helm-unittest#install)

Then you can simply run

```bash
make test-helm
```

## Useful `make` commands

> 🚶‍This part was moved to `make help` command. Run it to see all the available commands and their descriptions

## Setting environment variables

If you need to override any additional environment variables, you should set these in a root `.env.dev` file.
This file is automatically picked up by the OnCall engine Docker containers. This file is ignored from source control
and also overrides any defaults that are set in other `.env*` files

## Slack application setup

For Slack app configuration check our docs: <https://grafana.com/docs/oncall/latest/open-source/#slack-setup>

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

```bash
LDFLAGS="-L$(brew --prefix openssl@1.1)/lib" CFLAGS="-I$(brew --prefix openssl@1.1)/include" pip install `cat engine/requirements.txt | grep cryptography`
```

### django.db.utils.OperationalError: (1366, "Incorrect string value")

**Problem:**

```bash
django.db.utils.OperationalError: (1366, "Incorrect string value: '\\xF0\\x9F\\x98\\x8A\\xF0\\x9F...' for column 'cached_name' at row 1")
```

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

```bash
Error response from daemon: open /var/lib/docker/overlay2/ac57b871108ee1b98ff4455e36d2175eae90cbc7d4c9a54608c0b45cfb7c6da5/committed: is a directory
make: *** [start] Error 1
```

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

### Removing a nullable field from a model

> This only works for nullable fields (fields with `null=True` in the field definition).
>
> DO NOT USE THIS APPROACH FOR NON-NULLABLE FIELDS, IT CAN BREAK THINGS!

1. Remove all usages of the field you want to remove. Make sure the field is not used anywhere, including filtering,
   querying, or explicit field referencing from views, models, forms, serializers, etc.
2. Remove the field from the model definition.
3. Generate migrations using the following management command:

   ```python
   python manage.py remove_field <APP_LABEL> <MODEL_NAME> <FIELD_NAME>
   ```

   Example: `python manage.py remove_field alerts AlertReceiveChannel restricted_at`

   This command will generate two migrations that **MUST BE DEPLOYED IN TWO SEPARATE RELEASES**:

   - Migration #1 will remove the field from Django's state, but not from the database. Release #1 must include
     migration #1, and must not include migration #2.
   - Migration #2 will remove the field from the database. Stash this migration for use in a future release.

4. Make release #1 (removal of the field + migration #1). Once released and deployed, Django will not be
   aware of this field anymore, but the field will be still present in the database. This allows for a gradual migration,
   where the field is no longer used in new code, but still exists in the database for backward compatibility with old code.
5. In any subsequent release, include migration #2 (the one that removes the field from the database).
6. After releasing and deploying migration #2, the field will be removed both from the database and Django state,
   without backward compatibility issues or downtime 🎉

## Autogenerating TS types based on OpenAPI schema

| :warning: WARNING                                                                           |
| :------------------------------------------------------------------------------------------ |
| Transition to this approach is [in progress](https://github.com/grafana/oncall/issues/3338) |

### Overview

In order to automate types creation and prevent API usage pitfalls, OnCall project is using the following approach:

1. OnCall Engine (backend) exposes OpenAPI schema
2. OnCall Grafana Plugin (frontend) autogenerates TS type definitions based on it
3. OnCall Grafana Plugin (frontend) uses autogenerated types as a single source of truth for
   any backend-related interactions (url paths, request bodies, params, response payloads)

### Instruction

1. Whenever API contract changes, run `yarn generate-types` from `grafana-plugin` directory
2. Then you can start consuming types and you can use fully typed http client:

   ```ts
   import { ApiSchemas } from "network/oncall-api/api.types";
   import { onCallApi } from "network/oncall-api/http-client";

   const {
     data: { results },
   } = await onCallApi().GET("/alertgroups/");
   const alertGroups: Array<ApiSchemas["AlertGroup"]> = results;
   ```

3. [Optional] If there is any property that is not yet exposed in OpenAPI schema and you already want to use it,
   you can append missing properties to particular schemas by editing
   `grafana-plugin/src/network/oncall-api/types-generator/custom-schemas.ts` file:

   ```ts
   export type CustomApiSchemas = {
     Alert: {
       propertyMissingInOpenAPI: string;
     };
     AlertGroup: {
       anotherPropertyMissingInOpenAPI: number[];
     };
   };
   ```

   Then add their names to `CUSTOMIZED_SCHEMAS` array in `grafana-plugin/src/network/oncall-api/types-generator/generate-types.ts`:

   ```ts
   const CUSTOMIZED_SCHEMAS = ["Alert", "AlertGroup"];
   ```

   The outcome is that autogenerated schemas will be modified as follows:

   ```ts
   import type { CustomApiSchemas } from './types-generator/custom-schemas';

   export interface components {
       schemas: {
           Alert: CustomApiSchemas['Alert'] & {
               readonly id: string;
               ...
           };
           AlertGroup: CustomApiSchemas['AlertGroup'] & {
               readonly pk: string;
               ...
           },
           ...
       }
   }
   ```

## System components

```mermaid
flowchart TD
    client[Monitoring System]
    third_party["Slack, Twilio, 
           3rd party services.."]
    server[Server]
    celery[Celery Worker]
    db[(SQL Database)]
    redis[("Cache
            (Redis)")]
    broker[("AMPQ Broker
             (Redis or RabbitMQ)")]
    
    subgraph OnCall Backend
    server <--> redis
    server <--> db
    server -->|"Schedule tasks 
                with ETA"| broker
    broker -->|"Fetch tasks"| celery
    celery --> db

    end
    subgraph Grafana Stack
    plugin["OnCall Frontend 
            Plugin"]
    proxy[Plugin Proxy]
    api[Grafana API]
    plugin --> proxy --> server
    api --> server
    end

    client -->|Alerts| server
    third_party -->|"Statuses, 
               events"| server
    celery -->|"Notifications, 
                Outgoing Webhooks"| third_party
```
