# Change Log

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
