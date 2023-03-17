---
aliases:
  - /docs/oncall/latest/oncall-api-reference/schedules/
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/schedules/
title: Schedule HTTP API
weight: 1200
---

# Schedule HTTP API

## Create a schedule

```shell
curl "{{API_URL}}/api/v1/schedules/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "name": "Demo schedule iCal",
      "ical_url_primary": "https://example.com/meow_calendar.ics",
      "slack": {
          "channel_id": "MEOW_SLACK_ID",
          "user_group_id": "MEOW_SLACK_ID"
      }
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "SBM7DV7BKFUYU",
  "name": "Demo schedule iCal",
  "type": "ical",
  "team_id": null,
  "ical_url_primary": "https://example.com/meow_calendar.ics",
  "ical_url_overrides": "https://example.com/meow_calendar_overrides.ics",
  "on_call_now": ["U4DNY931HHJS5"],
  "slack": {
    "channel_id": "MEOW_SLACK_ID",
    "user_group_id": "MEOW_SLACK_ID"
  }
}
```

<!-- markdownlint-disable MD013 -->

| Parameter            | Unique |     Required     | Description                                                                                                                                                                                                                                         |
| -------------------- | :----: | :--------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`               |  Yes   |       Yes        | Schedule name.                                                                                                                                                                                                                                      |
| `type`               |   No   |       Yes        | Schedule type. May be `ical` (used for iCalendar integration) or `calendar` (used for manually created on-call shifts).                                                                                                                             |
| `team_id`            |   No   |        No        | ID of the team.                                                                                                                                                                                                                                     |
| `time_zone`          |   No   |     Optional     | Schedule time zone. Is used for manually added on-call shifts in Schedules with type `calendar`. Default time zone is `UTC`. For more information about time zones, see [time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). |
| `ical_url_primary`   |   No   | If type = `ical` | URL of external iCal calendar for schedule with type `ical`.                                                                                                                                                                                        |
| `ical_url_overrides` |   No   |     Optional     | URL of external iCal calendar for schedule with any type. Events from this calendar override events from primary calendar or from on-call shifts.                                                                                                   |
| `slack`              |   No   |     Optional     | Dictionary with Slack-specific settings for a schedule. Includes `channel_id` and `user_group_id` fields, that take a channel ID and a user group ID from Slack.                                                                                    |
| `shifts`             |   No   |     Optional     | List of shifts. Used for manually added on-call shifts in Schedules with type `calendar`.                                                                                                                                                           |

<!-- markdownlint-enable MD013 -->

**HTTP request**

`POST {{API_URL}}/api/v1/schedules/`

## Get a schedule

```shell
curl "{{API_URL}}/api/v1/schedules/SBM7DV7BKFUYU/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
```

The above command returns JSON structured in the following way:

```json
{
  "id": "SBM7DV7BKFUYU",
  "name": "Demo schedule iCal",
  "type": "ical",
  "team_id": null,
  "ical_url_primary": "https://example.com/meow_calendar.ics",
  "ical_url_overrides": "https://example.com/meow_calendar_overrides.ics",
  "on_call_now": ["U4DNY931HHJS5"],
  "slack": {
    "channel_id": "MEOW_SLACK_ID",
    "user_group_id": "MEOW_SLACK_ID"
  }
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/schedules/<SCHEDULE_ID>/`

## List schedules

```shell
curl "{{API_URL}}/api/v1/schedules/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "SBM7DV7BKFUYU",
      "name": "Demo schedule iCal",
      "type": "ical",
      "team_id": null,
      "ical_url_primary": "https://example.com/meow_calendar.ics",
      "ical_url_overrides": "https://example.com/meow_calendar_overrides.ics",
      "on_call_now": ["U4DNY931HHJS5"],
      "slack": {
        "channel_id": "MEOW_SLACK_ID",
        "user_group_id": "MEOW_SLACK_ID"
      }
    },
    {
      "id": "S3Z477AHDXTMF",
      "name": "Demo schedule Calendar",
      "type": "calendar",
      "team_id": null,
      "time_zone": "America/New_York",
      "on_call_now": ["U4DNY931HHJS5"],
      "shifts": ["OH3V5FYQEYJ6M", "O9WTH7CKM3KZW"],
      "ical_url_overrides": null,
      "slack": {
        "channel_id": "MEOW_SLACK_ID",
        "user_group_id": "MEOW_SLACK_ID"
      }
    }
  ]
}
```

The following available filter parameter should be provided as a `GET` argument:

- `name` (Exact match)

**HTTP request**

`GET {{API_URL}}/api/v1/schedules/`

## Update a schedule

```shell
curl "{{API_URL}}/api/v1/schedules/SBM7DV7BKFUYU/" \
  --request PUT \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
    "name": "Demo schedule iCal",
    "ical_url": "https://example.com/meow_calendar.ics",
    "slack": {
        "channel_id": "MEOW_SLACK_ID"
    }
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "SBM7DV7BKFUYU",
  "name": "Demo schedule iCal",
  "type": "ical",
  "team_id": null,
  "ical_url_primary": "https://example.com/meow_calendar.ics",
  "ical_url_overrides": "https://example.com/meow_calendar_overrides.ics",
  "on_call_now": ["U4DNY931HHJS5"],
  "slack": {
    "channel_id": "MEOW_SLACK_ID",
    "user_group_id": "MEOW_SLACK_ID"
  }
}
```

**HTTP request**

`PUT {{API_URL}}/api/v1/schedules/<SCHEDULE_ID>/`

## Delete a schedule

```shell
curl "{{API_URL}}/api/v1/schedules/SBM7DV7BKFUYU/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

**HTTP request**

`DELETE {{API_URL}}/api/v1/schedules/<SCHEDULE_ID>/`
