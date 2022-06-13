* [Developer quickstart](#developer-quickstart)
  * [Backend setup](#backend-setup)
  * [Frontend setup](#frontend-setup)
  * [Slack application setup](#slack-application-setup)
* [Troubleshooting](#troubleshooting)
  * [ld: library not found for -lssl](#ld-library-not-found-for--lssl)
  * [Could not build wheels for cryptography which use PEP 517 and cannot be installed directly](#could-not-build-wheels-for-cryptography-which-use-pep-517-and-cannot-be-installed-directly)
  * [django.db.utils.OperationalError: (1366, "Incorrect string value ...")](#djangodbutilsoperationalerror-1366-incorrect-string-value-)
  * [Empty queryset when filtering against datetime field](#empty-queryset-when-filtering-against-datetime-field)
* [Hints](#hints)
  * [Building the all-in-one docker container](#building-the-all-in-one-docker-container)
  * [Running Grafana with plugin (frontend) folder mounted for dev purposes](#running-grafana-with-plugin-frontend-folder-mounted-for-dev-purposes)
  * [How to recreate the local database](#recreating-the-local-database)
  * [Running tests locally](#running-tests-locally)
* [IDE Specific Instructions](#ide-specific-instructions)
  * [PyCharm](#pycharm)
  
## Developer quickstart

### Code style

- [isort](https://github.com/PyCQA/isort), [black](https://github.com/psf/black) and [flake8](https://github.com/PyCQA/flake8) are used to format backend code
- [eslint](https://eslint.org) and [stylelint](https://stylelint.io) are used to format frontend code
- To run formatters and linters on all files: `pre-commit run --all-files`
- To install pre-commit hooks: `pre-commit install`

### Backend setup

1. Start stateful services (RabbitMQ, Redis, Grafana with mounted plugin folder)
```bash
docker-compose -f docker-compose-developer.yml up -d
```

2. Prepare a python environment:
```bash
# Create and activate the virtual environment
python3.9 -m venv venv && source venv/bin/activate

# Verify that python has version 3.9.x
python --version

# Make sure you have latest pip and wheel support
pip install -U pip wheel

# Copy and check .env file.
cp .env.example .env

# Apply .env to current terminal.
# For PyCharm it's better to use https://plugins.jetbrains.com/plugin/7861-envfile/
export $(grep -v '^#' .env | xargs -0)

# Install dependencies.
# Hint: there is a known issue with uwsgi. It's not used in the local dev environment. Feel free to comment it in `engine/requirements.txt`.
cd engine && pip install -r requirements.txt

# Migrate the DB:
python manage.py migrate

# Create user for django admin panel (if you need it):
python manage.py createsuperuser
```


3. Launch the backend:
```bash
# Http server:
python manage.py runserver

# Worker for background tasks (run it in the parallel terminal, don't forget to export .env there)
python manage.py start_celery

# Additionally you could launch the worker with periodic tasks launcher (99% you don't need this)
celery -A engine beat -l info
```

4. All set! Check out internal API endpoints at http://localhost:8000/.


### Frontend setup

1. Make sure you have [NodeJS v.14+ < 17](https://nodejs.org/) and [yarn](https://yarnpkg.com/) installed.

2. Install the dependencies with `yarn` and launch the frontend server (on port `3000` by default)
```bash
cd grafana-plugin
yarn install
yarn
yarn watch
```

3. Ensure /grafana-plugin/provisioning has no grafana-plugin.yml
   
4. Generate an invitation token:
```bash
cd engine;
python manage.py issue_invite_for_the_frontend --override
```
... or use output of all-in-one docker container described in the README.md.

5. Open Grafana in the browser http://localhost:3000 (login: oncall, password: oncall) notice OnCall Plugin is not enabled, navigate to Configuration->Plugins and click Grafana OnCall

6. Some configuration fields will appear be available. Fill them out and click Initialize OnCall
```
OnCall API URL: 
http://host.docker.internal:8000

Invitation Token (Single use token to connect Grafana instance):
Response from the invite generator command (check above)

Grafana URL (URL OnCall will use to talk to Grafana instance):
http://localhost:3000
```

NOTE: you may not have `host.docker.internal` available, in that case you can get the
host IP from inside the container by running:
```bash
/sbin/ip route|awk '/default/ { print $3 }'

# Alternatively add host.docker.internal as an extra_host for grafana in docker-compose-developer.yml
extra_hosts:
  - "host.docker.internal:host-gateway"

```

### Slack application setup

This instruction is also applicable if you set up self-hosted OnCall.

1. Start a [localtunnel](https://github.com/localtunnel/localtunnel) reverse proxy to make oncall engine api accessible to slack (if you don't have OnCall backend accessible from https), 
```bash
# Choose the unique prefix instead of pretty-turkey-83
# Localtunnel will generate an url, e.g. https://pretty-turkey-83.loca.lt
# it is referred as <ONCALL_ENGINE_PUBLIC_URL> below
lt --port 8000 -s pretty-turkey-83 --print-requests
```

2. [Create a Slack Workspace](https://slack.com/create) for development.

3. Go to https://api.slack.com/apps and click Create New App button

4. Select `From an app manifest` option and choose the right workspace

5. Copy and paste the following block with the correct <YOUR_BOT_NAME> and <ONCALL_ENGINE_PUBLIC_URL> fields

<details>
  <summary>Click to expand!</summary>

  ```yaml
  _metadata:
    major_version: 1
    minor_version: 1
  display_information:
    name: <YOUR_BOT_NAME>
  features:
    app_home:
      home_tab_enabled: true
      messages_tab_enabled: true
      messages_tab_read_only_enabled: false
    bot_user:
      display_name: <YOUR_BOT_NAME>
      always_online: true
    shortcuts:
      - name: Create a new incident
        type: message
        callback_id: incident_create
        description: Creates a new OnCall incident
      - name: Add to postmortem
        type: message
        callback_id: add_postmortem
        description: Add this message to postmortem
    slash_commands:
      - command: /oncall
        url: <ONCALL_ENGINE_PUBLIC_URL>/slack/interactive_api_endpoint/
        description: oncall
        should_escape: false
  oauth_config:
    redirect_urls:
      - <ONCALL_ENGINE_PUBLIC_URL>/api/internal/v1/complete/slack-install-free/
      - <ONCALL_ENGINE_PUBLIC_URL>/api/internal/v1/complete/slack-login/
    scopes:
      user:
        - channels:read
        - chat:write
        - identify
        - users.profile:read
      bot:
        - app_mentions:read
        - channels:history
        - channels:read
        - chat:write
        - chat:write.customize
        - chat:write.public
        - commands
        - files:write
        - groups:history
        - groups:read
        - im:history
        - im:read
        - im:write
        - mpim:history
        - mpim:read
        - mpim:write
        - reactions:write
        - team:read
        - usergroups:read
        - usergroups:write
        - users.profile:read
        - users:read
        - users:read.email
        - users:write
  settings:
    event_subscriptions:
      request_url: <ONCALL_ENGINE_PUBLIC_URL>/slack/event_api_endpoint/
      bot_events:
        - app_home_opened
        - app_mention
        - channel_archive
        - channel_created
        - channel_deleted
        - channel_rename
        - channel_unarchive
        - member_joined_channel
        - message.channels
        - message.im
        - subteam_created
        - subteam_members_changed
        - subteam_updated
        - user_change
    interactivity:
      is_enabled: true
      request_url: <ONCALL_ENGINE_PUBLIC_URL>/slack/interactive_api_endpoint/
    org_deploy_enabled: false
    socket_mode_enabled: false
  ```
</details>

6. Click `Install to workspace` button to generate the credentials 

6. Populate the environment with variables related to Slack

    In your `.env` file, fill out the following variables:
    
    ```
    SLACK_CLIENT_OAUTH_ID = Basic Information -> App Credentials -> Client ID
    SLACK_CLIENT_OAUTH_SECRET = Basic Information -> App Credentials -> Client Secret
    SLACK_API_TOKEN = OAuth & Permissions -> Bot User OAuth Token
    SLACK_INSTALL_RETURN_REDIRECT_HOST = https://pretty-turkey-83.loca.lt
    ```

    Don't forget to export variables from the `.env` file and restart the server!

7. Edit `grafana-plugin/grafana-plugin.yml` to set `onCallApiUrl` fields with localtunnel url
    ```
        onCallApiUrl: https://pretty-turkey-83.loca.lt
    ```
   
   or set BASE_URL Env variable through web interface.

8. Edit grafana-plugin/src/plugin.json to add `Bypass-Tunnel-Reminder` header section for all existing routes 
    > this headers required for the local development only, otherwise localtunnel blocks requests from grafana plugin, An alternative to this is you can modify your user-agent in your browser to bypass the tunnel warning, it only filters the common browsers.
 
    ```
        {
         "path": ...,
         ...
         "headers": [
           ...
           {
             "name": "Bypass-Tunnel-Reminder",
             "content": "True"
           }
         ]
       },
    ```
9. Rebuild the plugin
    ```
    yarn watch
    ```
10. Restart grafana instance

11. All set! Go to Slack and check if your application is functional.

## Troubleshooting

### ld: library not found for -lssl

**Problem:**
```
pip install -r requirements.txt
...
    ld: library not found for -lssl
    clang: error: linker command failed with exit code 1 (use -v to see invocation)
    error: command 'gcc' failed with exit status 1
...
```
**Solution:**

```
export LDFLAGS=-L/usr/local/opt/openssl/lib
pip install -r requirements.txt
```

### Could not build wheels for cryptography which use PEP 517 and cannot be installed directly

Happens on Apple Silicon

**Problem:**
```
  build/temp.macosx-12-arm64-3.9/_openssl.c:575:10: fatal error: 'openssl/opensslv.h' file not found
  #include <openssl/opensslv.h>
           ^~~~~~~~~~~~~~~~~~~~
  1 error generated.
  error: command '/usr/bin/clang' failed with exit code 1
  ----------------------------------------
  ERROR: Failed building wheel for cryptography
```
**Solution:**
```
LDFLAGS="-L$(brew --prefix openssl@1.1)/lib" CFLAGS="-I$(brew --prefix openssl@1.1)/include" pip install `cat requirements.txt | grep cryptography`
```

### django.db.utils.OperationalError: (1366, "Incorrect string value ...")

**Problem:**
```
django.db.utils.OperationalError: (1366, "Incorrect string value: '\\xF0\\x9F\\x98\\x8A\\xF0\\x9F...' for column 'cached_name' at row 1")
```

**Solution:**

Recreate the database with the correct encoding.
 
 ### Grafana OnCall plugin does not show up in plugin list
 
**Problem:**
I've run `yarn watch` in `grafana_plugin` but I do not see Grafana OnCall in the list of plugins
 
**Solution:**
If it is the first time you have run `yarn watch` and it was run after starting Grafana in docker-compose; Grafana will not have detected a plugin to fix: `docker-compose -f developer-docker-compose.yml restart grafana`
 
## Hints:

### Building the all-in-one docker container

```bash
cd engine;
docker build -t grafana/oncall-all-in-one -f Dockerfile.all-in-one .
```

### Running Grafana with plugin (frontend) folder mounted for dev purposes

Do it only after you built frontend at least once! Also developer-docker-compose.yml has similar Grafana included.
```bash
docker run --rm -it -p 3000:3000 -v "$(pwd)"/grafana-plugin:/var/lib/grafana/plugins/grafana-plugin -e GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS=grafana-oncall-app --name=grafana grafana/grafana:8.3.2
```
Credentials: admin/admin

### Running tests locally

```
# in the engine directory, with the virtualenv activated
pytest --ds=settings.dev
```

## IDE Specific Instructions

### PyCharm
1. Create venv and copy .env file
   ```bash
   python3.9 -m venv venv
   cp .env.example .env
   ```
2. Open the project in PyCharm
3. Settings &rarr; Project OnCall
   - In Python Interpreter click the gear and create a new Virtualenv from existing environment selecting the venv created in Step 1.
   - In Project Structure make sure the project root is the content root and add /engine to Sources
4. Under Settings &rarr; Languages & Frameworks  &rarr; Django
   - Enable Django support
   - Set Django project root to /engine
   - Set Settings to settings/dev.py
5. Create a new Django Server run configuration to Run/Debug the engine
   - Use a plugin such as EnvFile to load the .env file

## Update drone build
The .drone.yml build file must be signed when changes are made to it.  Follow these steps:

If you have not installed drone CLI follow [these instructions](https://docs.drone.io/cli/install/)

To sign the .drone.yml file:
```bash
export DRONE_SERVER=https://drone.grafana.net

# Get your drone token from https://drone.grafana.net/account
export DRONE_TOKEN=<Your DRONE_TOKEN>

drone sign --save grafana/oncall .drone.yml
```
