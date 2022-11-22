# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.1.3 (2022-11-22)

- Bug Fixes

### Changed

- For OSS installations of OnCall, initial configuration is now simplified. When running for local development, you no longer need to configure the plugin via the UI. This is achieved through passing one environment variable to both the backend & frontend containers, both of which have been preconfigured for you in `docker-compose-developer.yml`.
  - The Grafana API URL **must be** passed as an environment variable, `GRAFANA_API_URL`, to the OnCall backend (and can be configured by updating this env var in your `./dev/.env.dev` file)
  - The OnCall API URL can optionally be passed as an environment variable, `ONCALL_API_URL`, to the OnCall UI. If the environment variable is found, the plugin will "auto-configure", otherwise you will be shown a simple configuration form to provide this info.
- For Helm installations, if you are running Grafana externally (eg. `grafana.enabled` is set to `false` in your `values.yaml`), you will now be required to specify `externalGrafana.url` in `values.yaml`.
- `make start` will now idempotently check to see if a "127.0.0.1 grafana" record exists in `/etc/hosts` (using a tool called [`hostess`](https://github.com/cbednarski/hostess)). This is to support using `http://grafana:3000` as the `Organization.grafana_url` in two scenarios:
  - `oncall_engine`/`oncall_celery` -> `grafana` Docker container communication
  - public URL generation. There are some instances where `Organization.grafana_url` is referenced to generate public URLs to a Grafana plugin page. Without the `/etc/hosts` record, navigating to `http://grafana:3000/some_page` in your browser, you would obviously get an error from your browser.

## v1.1.2 (2022-11-18)

- Bug Fixes

## v1.1.1 (2022-11-16)

- Compatibility with Grafana 9.3.0
- Bug Fixes

## v1.0.52 (2022-11-09)

- Allow use of API keys as alternative to account auth token for Twilio
- Remove `grafana_plugin_management` Django app
- Enable new schedules UI
- Bug fixes

## v1.0.51 (2022-11-05)

- Bug Fixes

## v1.0.50 (2022-11-03)

- Updates to documentation
- Improvements to web schedules
- Bug fixes

## v1.0.49 (2022-11-01)

- Enable SMTP email backend by default
- Fix Grafana sidebar frontend bug

## v1.0.48 (2022-11-01)

- verify_number management command
- chatops page redesign

## v1.0.47 (2022-11-01)

- Bug fixes

## v1.0.46 (2022-10-28)

- Bug fixes
- remove `POST /api/internal/v1/custom_buttons/{id}/action` endpoint

## v1.0.45 (2022-10-27)

- Bug fix to revert commit which removed unused engine code

## v1.0.44 (2022-10-26)

- Bug fix for an issue that was affecting phone verification

## v1.0.43 (2022-10-25)

- Bug fixes

## v1.0.42 (2022-10-24)

- Fix posting resolution notes to Slack

## v1.0.41 (2022-10-24)

- Add personal email notifications
- Bug fixes

## v1.0.40 (2022-10-05)

- Improved database and celery backends support
- Added script to import PagerDuty users to Grafana
- Bug fixes

## v1.0.39 (2022-10-03)

- Fix issue in v1.0.38 blocking the creation of schedules and webhooks in the UI

## v1.0.38 (2022-09-30)

- Fix exception handling for adding resolution notes when slack and oncall users are out of sync.
- Fix all day events showing as having gaps in slack notifications
- Improve plugin configuration error message readability
- Add `telegram` key to `permalinks` property in `AlertGroup` public API response schema

## v1.0.37 (2022-09-21)

- Improve API token creation form
- Fix alert group bulk action bugs
- Add `permalinks` property to `AlertGroup` public API response schema
- Scheduling system bug fixes
- Public API bug fixes

## v1.0.36 (2022-09-12)

- Alpha web schedules frontend/backend updates
- Bug fixes

## v1.0.35 (2022-09-07)

- Bug fixes

## v1.0.34 (2022-09-06)

- Fix schedule notification spam

## v1.0.33 (2022-09-06)

- Add raw alert view
- Add GitHub star button for OSS installations
- Restore alert group search functionality
- Bug fixes

## v1.0.32 (2022-09-01)

- Bug fixes

## v1.0.31 (2022-09-01)

- Bump celery version
- Fix oss to cloud connection

## v1.0.30 (2022-08-31)

- Bug fix: check user notification policy before access

## v1.0.29 (2022-08-31)

- Add arm64 docker image

## v1.0.28 (2022-08-31)

- Bug fixes

## v1.0.27 (2022-08-30)

- Bug fixes

## v1.0.26 (2022-08-26)

- Insight log's format fixes
- Remove UserNotificationPolicy auto-recreating

## v1.0.25 (2022-08-24)

- Bug fixes

## v1.0.24 (2022-08-24)

- Insight logs
- Default DATA_UPLOAD_MAX_MEMORY_SIZE to 1mb

## v1.0.23 (2022-08-23)

- Bug fixes

## v1.0.22 (2022-08-16)

- Make STATIC_URL configurable from environment variable

## v1.0.21 (2022-08-12)

- Bug fixes

## v1.0.19 (2022-08-10)

- Bug fixes

## v1.0.15 (2022-08-03)

- Bug fixes

## v1.0.13 (2022-07-27)

- Optimize alert group list view
- Fix a bug related to Twilio setup

## v1.0.12 (2022-07-26)

- Update push-notifications dependency
- Rework how absolute URLs are built
- Fix to show maintenance windows per team
- Logging improvements
- Internal api to get a schedule final events

## v1.0.10 (2022-07-22)

- Speed-up of alert group web caching
- Internal api for OnCall shifts

## v1.0.9 (2022-07-21)

- Frontend bug fixes & improvements
- Support regex_replace() in templates
- Bring back alert group caching and list view

## v1.0.7 (2022-07-18)

- Backend & frontend bug fixes
- Deployment improvements
- Reshape webhook payload for outgoing webhooks
- Add escalation chain usage info on escalation chains page
- Improve alert group list load speeds and simplify caching system

## v1.0.6 (2022-07-12)

- Manual Incidents enabled for teams
- Fix phone notifications for OSS
- Public API improvements

## v1.0.5 (2022-07-06)

- Bump Django to 3.2.14
- Fix PagerDuty iCal parsing

## 1.0.4 (2022-06-28)

- Allow Telegram DMs without channel connection.

## 1.0.3 (2022-06-27)

- Fix users public api endpoint. Now it returns users with all roles.
- Fix redundant notifications about gaps in schedules.
- Frontend fixes.

## 1.0.2 (2022-06-17)

- Fix Grafana Alerting integration to handle API changes in Grafana 9
- Improve public api endpoint for outgoing webhooks (/actions) by adding ability to create, update and delete outgoing webhook instance

## 1.0.0 (2022-06-14)

- First Public Release

## 0.0.71 (2022-06-06)

- Initial Commit Release
