- [Developer quickstart](#developer-quickstart)
  - [Running the project](#running-the-project)
  - [Running in Docker](#running-in-docker)
    - [`COMPOSE_PROFILES`](#compose_profiles)
  - [Useful `make` commands](#useful-make-commands)
  - [Setting environment variables](#setting-environment-variables)
  - [Slack application setup](#slack-application-setup)
  - [Update drone build](#update-drone-build)
- [IDE Specific Instructions](#ide-specific-instructions)
  - [PyCharm](#pycharm)

## Developer quickstart

Related: [How to develop integrations](/engine/config_integrations/README.md)

### Running the project

1. Firstly, ensure that you have `docker` [installed](https://docs.docker.com/get-docker/) and running on your machine.
2. Run `make start`. By default this will run everything in Docker, using SQLite as the database and Redis as the message broker/cache. See [Running in Docker](#running-in-docker) below for more details on how to swap out/disable which components are run in Docker.
3. Open Grafana in a browser [here](http://localhost:3000/plugins/grafana-oncall-app) (login: `oncall`, password: `oncall`).
4. You should now see the OnCall plugin configuration page. Fill out the configuration options as follows:

- Invite token: run `make get-invite-token` and copy/paste the token that gets printed out
- OnCall backend URL: http://host.docker.internal:8080 (this is the URL that is running the OnCall API; it should be accessible from Grafana)
- Grafana URL: http://grafana:3000 (this is the URL OnCall will use to talk to the Grafana Instance)

5. Enjoy! Check our [OSS docs](https://grafana.com/docs/grafana-cloud/oncall/open-source/) if you want to set up Slack, Telegram, Twilio or SMS/calls through Grafana Cloud.
6. (Optional) Install `pre-commit` hooks by running `make install-precommit-hook`

### Running in Docker

By default everything runs inside Docker. These options can be modified by configuring `COMPOSE_PROFILE`.

#### `COMPOSE_PROFILES`

This configuration option represents a comma-separated list of [`docker-compose` profiles](https://docs.docker.com/compose/profiles/). It allows you to swap-out, or disable, certain components in Docker.

This option can be configured in two ways:

1. Setting a `COMPOSE_PROFILE` environment variable in `.env.dev`. This allows you to avoid having to set `COMPOSE_PROFILE` for each `make` command you execute afterwards.
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

### Useful `make` commands

See [`COMPOSE_PROFILES`](#compose_profiles) for more information on what this option is and how to configure it.

```bash
make stop # stop all of the docker containers
make restart # restart all docker containers

# this will remove all of the images, containers, volumes, and networks
# associated with your local OnCall developer setup
make cleanup

make get-invite-token # generate an invitation token
make start-celery-beat # start celery beat
make purge-queues # purge celery queues
make shell # starts an OnCall engine Django shell
make dbshell # opens a DB shell
make test # run backend tests

# run both frontend and backend linters
# may need to run `yarn install` from within `grafana-plugin` to install several `pre-commit` dependencies
make lint
```

### Setting environment variables

If you need to override any additional environment variables, you should set these in a root `.env.dev` file. This file is automatically picked up by the OnCall engine Docker containers. This file is ignored from source control and also overrides any defaults that are set in other `.env*` files

### Slack application setup

For Slack app configuration check our docs: https://grafana.com/docs/grafana-cloud/oncall/open-source/#slack-setup

### Update drone build

The .drone.yml build file must be signed when changes are made to it. Follow these steps:

If you have not installed drone CLI follow [these instructions](https://docs.drone.io/cli/install/)

To sign the .drone.yml file:

```bash
export DRONE_SERVER=https://drone.grafana.net

# Get your drone token from https://drone.grafana.net/account
export DRONE_TOKEN=<Your DRONE_TOKEN>

drone sign --save grafana/oncall .drone.yml
```

## IDE Specific Instructions

### PyCharm

1. Create a Python virtual environment for the project, using your favorite tool (ex. [`venv`](https://docs.python.org/3.10/tutorial/venv.html) or [`pyenv-virtualenv`](https://github.com/pyenv/pyenv-virtualenv))
2. Open the project in PyCharm
3. Settings &rarr; Project OnCall
   - In Python Interpreter click the gear and create a new Virtualenv from existing environment selecting the venv created in Step 1.
   - In Project Structure make sure the project root is the content root and add /engine to Sources
4. Under Settings &rarr; Languages & Frameworks &rarr; Django
   - Enable Django support
   - Set Django project root to /engine
   - Set Settings to settings/dev.py
5. Create a new Django Server run configuration to Run/Debug the engine
   - Use a plugin such as EnvFile to load the .env.dev file
   - Change port from 8000 to 8080
