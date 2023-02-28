# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Fixed

- Fixed importing of global grafana styles ([672](https://github.com/grafana/oncall/issues/672))
- Fixed UI permission related bug where Editors could not export their user iCal link
- Fixed error when a shift is created using Etc/UTC as timezone
- Fixed issue with refresh ical file task not considering empty string values
- Schedules: Long popup does not fit screen & buttons unreachable & objects outside of the popup ([1002](https://github.com/grafana/oncall/issues/1002))
- Can't scroll on integration settings page ([415](https://github.com/grafana/oncall/issues/415))
- Team change in the Integration page always causes 403 ([1292](https://github.com/grafana/oncall/issues/1292))
- Schedules: Permalink doesn't work with multi-teams ([940](https://github.com/grafana/oncall/issues/940))
- Schedules list -> expanded schedule blows page width ([1293](https://github.com/grafana/oncall/issues/1293))

### Changed

- Moved reCAPTCHA to backend environment variable for more flexible configuration between different environments.
- Add pagination to schedule listing
- Show 100 latest alerts on alert group page ([1417](https://github.com/grafana/oncall/pull/1417))

## v1.1.29 (2023-02-23)

### Changed

- Allow creating schedules with type "web" using public API

### Fixed

- Fixed minor issue during the sync process where an HTTP 302 (redirect) status code from the Grafana
  instance would cause the sync to not properly finish

## v1.1.28 (2023-02-23)

### Fixed

- Fixed maintenance mode for Telegram and MSTeams

## v1.1.27 (2023-02-22)

### Added

- Added reCAPTCHA validation for requesting a mobile verification code

### Changed

- Added ratelimits for phone verification

### Fixed

- Fixed HTTP request to Google where when fetching an iCal, the response would sometimes contain HTML instead
  of the expected iCal data

## v1.1.26 (2023-02-20)

### Fixed

- Make alert group filters persistent ([482](https://github.com/grafana/oncall/issues/482))

### Changed

- Update phone verification error message

## v1.1.25 (2023-02-20)

### Fixed

- Fixed too long declare incident link in Slack

## v1.1.24 (2023-02-16)

### Added

- Add direct user paging ([823](https://github.com/grafana/oncall/issues/823))
- Add App Store link to web UI ([1328](https://github.com/grafana/oncall/pull/1328))

### Fixed

- Cleaning of the name "Incident" ([704](https://github.com/grafana/oncall/pull/704))
- Alert Group/Alert Groups naming polishing. All the names should be with capital letters
- Design polishing ([1290](https://github.com/grafana/oncall/pull/1290))
- Not showing contact details in User tooltip if User does not have edit/admin access
- Updated slack link account to redirect back to user profile instead of chatops

### Changed

- Incidents - Removed buttons column and replaced status with toggler ([#1237](https://github.com/grafana/oncall/issues/1237))
- Responsiveness changes across multiple pages (Incidents, Integrations, Schedules) ([#1237](https://github.com/grafana/oncall/issues/1237))
- Add pagination to schedule listing
- Link to source was added
- Header of Incident page was reworked: clickable labels instead of just names, users section was deleted
- "Go to Integration" button was deleted, because the functionality was moved to clickable labels

## v1.1.23 (2023-02-06)

### Fixed

- Fix bug with email case sensitivity for ICal on-call schedules ([1297](https://github.com/grafana/oncall/pull/1297))

## v1.1.22 (2023-02-03)

### Fixed

- Fix bug with root/dependant alert groups list api endpoint ([1284](https://github.com/grafana/oncall/pull/1284))
- Fixed NPE on teams switch

### Added

- Optimize alert and alert group public api endpoints and add filter by id ([1274](https://github.com/grafana/oncall/pull/1274))
- Enable mobile app backend by default on OSS

## v1.1.21 (2023-02-02)

### Added

- Add [`django-dbconn-retry` library](https://github.com/jdelic/django-dbconn-retry) to `INSTALLED_APPS` to attempt
  to alleviate occasional `django.db.utils.OperationalError` errors
- Improve alerts and alert group endpoint response time in internal API with caching ([1261](https://github.com/grafana/oncall/pull/1261))
- Optimize alert and alert group public api endpoints and add filter by id ([1274](https://github.com/grafana/oncall/pull/1274)
- Added Coming Soon for iOS on Mobile App screen

### Fixed

- Fix issue on Integrations where you were redirected back once escalation chain was loaded ([#1083](https://github.com/grafana/oncall/issues/1083))
  ([#1257](https://github.com/grafana/oncall/issues/1257))

## v1.1.20 (2023-01-30)

### Added

- Add involved users filter to alert groups listing page (+ mine shortcut)

### Changed

- Improve logging for creating contact point for Grafana Alerting integration

### Fixed

- Fix bugs related to creating contact point for Grafana Alerting integration
- Fix minor UI bug on OnCall users page where it would idefinitely show a "Loading..." message
- Only show OnCall user's table to users that are authorized
- Fixed NPE in ScheduleUserDetails component ([#1229](https://github.com/grafana/oncall/issues/1229))

## v1.1.19 (2023-01-25)

### Added

- Add Server URL below QR code for OSS for debugging purposes
- Add Slack slash command allowing to trigger a direct page via a manually created alert group
- Remove resolved and acknowledged filters as we switched to status ([#1201](https://github.com/grafana/oncall/pull/1201))
- Add sync with grafana on /users and /teams api calls from terraform plugin

### Changed

- Allow users with `viewer` role to fetch cloud connection status using the internal API ([#1181](https://github.com/grafana/oncall/pull/1181))
- When removing the Slack ChatOps integration, make it more explicit to the user what the implications of doing so are
- Improve performance of `GET /api/internal/v1/schedules` endpoint ([#1169](https://github.com/grafana/oncall/pull/1169))

### Fixed

- Removed duplicate API call, in the UI on plugin initial load, to `GET /api/internal/v1/alert_receive_channels`
- Increased plugin startup speed ([#1200](https://github.com/grafana/oncall/pull/1200))

## v1.1.18 (2023-01-18)

### Added

- Allow messaging backends to be enabled/disabled per organization ([#1151](https://github.com/grafana/oncall/pull/1151))

### Changed

- Send a Slack DM when user is not in channel ([#1144](https://github.com/grafana/oncall/pull/1144))

## v1.1.17 (2023-01-18)

### Changed

- Modified how the `Organization.is_rbac_permissions_enabled` flag is set,
  based on whether we are dealing with an open-source, or cloud installation
- Backend implementation to support direct user/schedule paging
- Changed documentation links to open in new window
- Remove helm chart signing
- Changed the user's profile modal to be wide for all tabs

### Added

- Added state filter for alert_group public API endpoint.
- Enrich user tooltip on Schedule page
- Added redirects for old-style links

### Fixed

- Updated typo in Helm chart values when specifying a custom Slack command name
- Fix for web schedules ical export to give overrides the right priority
- Fix for topnavbar to show initial loading inside PluginPage

## v1.1.16 (2023-01-12)

### Fixed

- Minor bug fix in how the value of `Organization.is_rbac_permissions_enabled` is determined

- Helm chart: default values file and documentation now reflect the correct key to set for the Slack
  slash command name, `oncall.slack.commandName`.

## v1.1.15 (2023-01-10)

### Changed

- Simplify and speed up slack rendering ([#1105](https://github.com/grafana/oncall/pull/1105))
- Faro - Point to 3 separate apps instead of just 1 for all environments ([#1110](https://github.com/grafana/oncall/pull/1110))
- Schedules - ([#1114](https://github.com/grafana/oncall/pull/1114), [#1109](https://github.com/grafana/oncall/pull/1109))

### Fixed

- Bugfix for topnavbar to place alerts inside PageNav ([#1040](https://github.com/grafana/oncall/pull/1040))

## v1.1.14 (2023-01-05)

### Changed

- Change wording from "incident" to "alert group" for the Telegram integration ([#1052](https://github.com/grafana/oncall/pull/1052))
- Soft-delete of organizations on stack deletion.

## v1.1.13 (2023-01-04)

### Added

- Integration with [Grafana Faro](https://grafana.com/docs/grafana-cloud/faro-web-sdk/) for Cloud Instances

## v1.1.12 (2023-01-03)

### Fixed

- Handle jinja exceptions during alert creation
- Handle exception for slack rate limit message

## v1.1.11 (2023-01-03)

### Fixed

- Fix error when schedule was not able to load
- Minor fixes

## v1.1.10 (2023-01-03)

### Fixed

- Minor fixes

## v1.1.9 (2023-01-03)

### Fixed

- Alert group query optimization
- Update RBAC scopes
- Fix error when schedule was not able to load
- Minor bug fixes

## v1.1.8 (2022-12-13)

### Added

- Added a `make` command, `enable-mobile-app-feature-flags`, which sets the backend feature flag in `./dev/.env.dev`,
  and updates a record in the `base_dynamicsetting` database table, which are needed to enable the mobile
  app backend features.

### Changed

- Added ability to change engine deployment update strategy via values in helm chart.
- removed APNS support
- changed the `django-push-notification` library from the `iskhakov` fork to the [`grafana` fork](https://github.com/grafana/django-push-notifications).
  This new fork basically patches an issue which affected the database migrations of this django app (previously the
  library would not respect the `USER_MODEL` setting when creating its tables and would instead reference the
  `auth_user` table.. which we don't want)
- add `--no-cache` flag to the `make build` command

### Fixed

- fix schedule UI types and permissions

## v1.1.7 (2022-12-09)

### Fixed

- Update fallback role for schedule write RBAC permission
- Mobile App Verification tab in the user settings modal is now hidden for users that do not have proper
  permissions to use it

## v1.1.6 (2022-12-09)

### Added

- RBAC permission support
- Add `time_zone` serializer validation for OnCall shifts and calendar/web schedules. In addition, add database migration
  to update values that may be invalid
- Add a `permalinks.web` field, which is a permalink to the alert group web app page, to the alert group internal/public
  API responses
- Added the ability to customize job-migrate `ttlSecondsAfterFinished` field in the helm chart

### Fixed

- Got 500 error when saving Outgoing Webhook ([#890](https://github.com/grafana/oncall/issues/890))
- v1.0.13 helm chart - update the OnCall backend pods image pull policy to "Always" (and explicitly set tag to `latest`).
  This should resolve some recent issues experienced where the frontend/backend versions are not aligned.

### Changed

- When editing templates for alert group presentation or outgoing webhooks, errors and warnings are now displayed in
  the UI as notification popups or displayed in the preview.
- Errors and warnings that occur when rendering templates during notification or webhooks will now render
  and display the error/warning as the result.

## v1.1.5 (2022-11-24)

### Added

- Added a QR code in the "Mobile App Verification" tab on the user settings modal to connect the mobile
  application to your OnCall instance

### Fixed

- UI bug fixes for Grafana 9.3 ([#860](https://github.com/grafana/oncall/pull/860))
- Bug fix for saving source link template ([#898](https://github.com/grafana/oncall/pull/898))

## v1.1.4 (2022-11-23)

### Fixed

- Bug fix for [#882](https://github.com/grafana/oncall/pull/882) which was causing the OnCall web calendars to not load
- Bug fix which, when installing the plugin, or after removing a Grafana API token, caused the plugin to not load properly

## v1.1.3 (2022-11-22)

- Bug Fixes

### Changed

- For OSS installations of OnCall, initial configuration is now simplified. When running for local development, you no
  longer need to configure the plugin via the UI. This is achieved through passing one environment variable to both the
  backend & frontend containers, both of which have been preconfigured for you in `docker-compose-developer.yml`.
  - The Grafana API URL **must be** passed as an environment variable, `GRAFANA_API_URL`, to the OnCall backend
    (and can be configured by updating this env var in your `./dev/.env.dev` file)
  - The OnCall API URL can optionally be passed as an environment variable, `ONCALL_API_URL`, to the OnCall UI.
    If the environment variable is found, the plugin will "auto-configure", otherwise you will be shown a simple
    configuration form to provide this info.
- For Helm installations, if you are running Grafana externally (eg. `grafana.enabled` is set to `false`
  in your `values.yaml`), you will now be required to specify `externalGrafana.url` in `values.yaml`.
- `make start` will now idempotently check to see if a "127.0.0.1 grafana" record exists in `/etc/hosts`
  (using a tool called [`hostess`](https://github.com/cbednarski/hostess)). This is to support using `http://grafana:3000`
  as the `Organization.grafana_url` in two scenarios:
  - `oncall_engine`/`oncall_celery` -> `grafana` Docker container communication
  - public URL generation. There are some instances where `Organization.grafana_url` is referenced to generate public
    URLs to a Grafana plugin page. Without the `/etc/hosts` record, navigating to `http://grafana:3000/some_page` in
    your browser, you would obviously get an error from your browser.

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
- Improve public api endpoint for outgoing webhooks (/actions) by adding ability to create, update and delete
  outgoing webhook instance

## 1.0.0 (2022-06-14)

- First Public Release

## 0.0.71 (2022-06-06)

- Initial Commit Release
