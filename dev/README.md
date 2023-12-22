# Developer quickstart

Related: [How to develop integrations](/engine/config_integrations/README.md)

## Quick Start using Kubernetes and Tilt

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

### Setting environment variables

If you need to override any additional environment variables, you should set these under the `env` object in your
`./dev/helm-local.dev.yml`. This file is automatically picked up by the OnCall engine containers.
This file is ignored from source control.

### Configuring Grafana

This section is applicable for when you would like to modify your Grafana instance's provisioning configuration.

For example, if you would like to enable the `topnav` feature toggle, you can modify your `./dev/grafana.dev.ini` as
such:

```ini
[feature_toggles]
enable = top_nav
```

The `grafana` container will have `./dev/grafana/grafana.dev.ini` volume mounted inside the container.

#### Modifying Provisioning Configuration

Files under `./dev/grafana/provisioning` are volume mounted into your Grafana container and allow you to easily
modify the instance's provisioning configuration. See the Grafana docs [here](https://grafana.com/docs/grafana/latest/administration/provisioning/#:~:text=You%20can%20manage%20data%20sources,match%20the%20provisioned%20configuration%20file.)
for more information.

#### Enabling RBAC for OnCall for local development

To run the project locally w/ RBAC for OnCall enabled, you will first need to run a `grafana-enterprise` container,
instead of a `grafana` container. Update your `grafana.image` config in `./dev/helm-local.dev.yml` to use said image.

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

#### Enabling OnCall prometheus exporter for local development

Update your `./dev/helm-local.dev.yml` as follows:

```yaml
env:
  - name: FEATURE_PROMETHEUS_EXPORTER_ENABLED
    value: "True"

prometheus:
  enabled: true
```

You may need to to make sure the new datasource is added by manually adding it using the UI. Prometheus will be running
in `localhost:9090` by default, using default settings.

### Django Silk Profiling

In order to setup [`django-silk`](https://github.com/jazzband/django-silk) for local profiling, perform the following
steps:

1. `make backend-debug-enable`
2. `make engine-manage CMD="createsuperuser"` - follow CLI prompts to create a Django superuser
3. Visit <http://localhost:8080/django-admin> and login using the credentials you created in step #2

You should now be able to visit <http://localhost:8080/silk/> and see the Django Silk UI.
See the `django-silk` documentation [here](https://github.com/jazzband/django-silk) for more information.

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
   import onCallApi from "network/oncall-api/http-client";

   const {
     data: { results },
   } = await onCallApi.GET("/alertgroups/");
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
