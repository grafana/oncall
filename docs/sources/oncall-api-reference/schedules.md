---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/schedules/
title: Schedules HTTP API
weight: 1200
---

# Schedules HTTP API

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

| Parameter            | Unique |     Required     | Description                                                                                                                                                                                                                                         |
| -------------------- | :----: | :--------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`               |  Yes   |       Yes        | Schedule name.                                                                                                                                                                                                                                      |
| `type`               |   No   |       Yes        | Schedule type. May be `ical` (used for iCalendar integration),  `calendar` (used for manually created on-call shifts) or `web` (for web UI managed schedules).                                                                                                                             |
| `team_id`            |   No   |        No        | ID of the team.                                                                                                                                                                                                                                     |
| `time_zone`          |   No   |       Yes     | Schedule time zone. It is used for manually added on-call shifts in Schedules with type `calendar`. Default time zone is `UTC`. For more information about time zones, see [time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). Not used for schedules with type `ical`. |
| `ical_url_primary`   |   No   | If type = `ical` | URL of external iCal calendar for schedule with type `ical`.                                                                                                                                                                                        |
| `ical_url_overrides` |   No   |     Optional     | URL of external iCal calendar for schedule with any type. Events from this calendar override events from primary calendar or from on-call shifts.                                                                                                   |
| `enable_web_overrides` |   No   |     Optional     | Whether to enable web overrides or not. Setting specific for API/Terraform based schedules (`calendar` type).                                                                                                   |
| `slack`              |   No   |     Optional     | Dictionary with Slack-specific settings for a schedule. Includes `channel_id` and `user_group_id` fields, that take a channel ID and a user group ID from Slack.                                                                                    |
| `shifts`             |   No   |     Optional     | List of shifts. Used for manually added on-call shifts in Schedules with type `calendar`.                                                                                                                                                           |

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
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
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

## Export a schedule's final shifts

**HTTP request**

```shell
curl "{{API_URL}}/api/v1/schedules/SBM7DV7BKFUYU/final_shifts?start_date=2023-01-01&end_date=2023-02-01" \
  --request GET \
  --header "Authorization: meowmeowmeow"
```

The above command returns JSON structured in the following way:

```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "user_pk": "UC2CHRT5SD34X",
      "user_email": "alice@example.com",
      "user_username": "alice",
      "shift_start": "2023-01-02T09:00:00Z",
      "shift_end": "2023-01-02T17:00:00Z"
    },
    {
      "user_pk": "U7S8H84ARFTGN",
      "user_email": "bob@example.com",
      "user_username": "bob",
      "shift_start": "2023-01-04T09:00:00Z",
      "shift_end": "2023-01-04T17:00:00Z"
    },
    {
      "user_pk": "UC2CHRT5SD34X",
      "user_email": "alice@example.com",
      "user_username": "alice",
      "shift_start": "2023-01-06T09:00:00Z",
      "shift_end": "2023-01-06T17:00:00Z"
    },
    {
      "user_pk": "U7S8H84ARFTGN",
      "user_email": "bob@example.com",
      "user_username": "bob",
      "shift_start": "2023-01-09T09:00:00Z",
      "shift_end": "2023-01-09T17:00:00Z"
    },
    {
      "user_pk": "UC2CHRT5SD34X",
      "user_email": "alice@example.com",
      "user_username": "alice",
      "shift_start": "2023-01-11T09:00:00Z",
      "shift_end": "2023-01-11T17:00:00Z"
    },
    {
      "user_pk": "U7S8H84ARFTGN",
      "user_email": "bob@example.com",
      "user_username": "bob",
      "shift_start": "2023-01-13T09:00:00Z",
      "shift_end": "2023-01-13T17:00:00Z"
    },
    {
      "user_pk": "UC2CHRT5SD34X",
      "user_email": "alice@example.com",
      "user_username": "alice",
      "shift_start": "2023-01-16T09:00:00Z",
      "shift_end": "2023-01-16T17:00:00Z"
    },
    {
      "user_pk": "U7S8H84ARFTGN",
      "user_email": "bob@example.com",
      "user_username": "bob",
      "shift_start": "2023-01-18T09:00:00Z",
      "shift_end": "2023-01-18T17:00:00Z"
    },
    {
      "user_pk": "UC2CHRT5SD34X",
      "user_email": "alice@example.com",
      "user_username": "alice",
      "shift_start": "2023-01-20T09:00:00Z",
      "shift_end": "2023-01-20T17:00:00Z"
    },
    {
      "user_pk": "U7S8H84ARFTGN",
      "user_email": "bob@example.com",
      "user_username": "bob",
      "shift_start": "2023-01-23T09:00:00Z",
      "shift_end": "2023-01-23T17:00:00Z"
    },
    {
      "user_pk": "UC2CHRT5SD34X",
      "user_email": "alice@example.com",
      "user_username": "alice",
      "shift_start": "2023-01-25T09:00:00Z",
      "shift_end": "2023-01-25T17:00:00Z"
    },
    {
      "user_pk": "U7S8H84ARFTGN",
      "user_email": "bob@example.com",
      "user_username": "bob",
      "shift_start": "2023-01-27T09:00:00Z",
      "shift_end": "2023-01-27T17:00:00Z"
    }
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
}
```

### Caveats

Some notes on the `start_date` and `end_date` query parameters:

- they are both required and should represent ISO 8601 formatted dates
- `end_date` must be greater than or equal to `start_date`
- `end_date` cannot be more than 365 days in the future from `start_date`

>**Note**: you can update schedules affecting past events, which will then
change the output you get from this endpoint. To get consistent information about past shifts
you must be sure to avoid updating rotations in-place but apply the changes as new rotations
with the right starting dates.

### Example script to transform data to .csv for all of your schedules

The following Python script will generate a `.csv` file, `oncall-report-2023-01-01-to-2023-01-31.csv`. This file will
contain three columns, `user_pk`, `user_email`, and `hours_on_call`, which represents how many hours each user was
on call during the period starting January 1, 2023 to January 31, 2023 (inclusive).

```python
import csv
import requests
from datetime import datetime

# CUSTOMIZE THE FOLLOWING VARIABLES
START_DATE = "2023-01-01"
END_DATE = "2023-01-31"
OUTPUT_FILE_NAME = f"oncall-report-{START_DATE}-to-{END_DATE}.csv"
MY_ONCALL_API_BASE_URL = "https://oncall-prod-us-central-0.grafana.net/oncall/api/v1/schedules"
MY_ONCALL_API_KEY = "meowmeowwoofwoof"

headers = {"Authorization": MY_ONCALL_API_KEY}
schedule_ids = [schedule["id"] for schedule in requests.get(MY_ONCALL_API_BASE_URL, headers=headers).json()["results"]]
user_on_call_hours = {}

for schedule_id in schedule_ids:
  response = requests.get(
    f"{MY_ONCALL_API_BASE_URL}/{schedule_id}/final_shifts?start_date={START_DATE}&end_date={END_DATE}",
    headers=headers)

  for final_shift in response.json()["results"]:
    user_pk = final_shift["user_pk"]
    end = datetime.fromisoformat(final_shift["shift_end"])
    start = datetime.fromisoformat(final_shift["shift_start"])
    shift_time_in_seconds = (end - start).total_seconds()
    shift_time_in_hours = shift_time_in_seconds / (60 * 60)

    if user_pk in user_on_call_hours:
      user_on_call_hours[user_pk]["hours_on_call"] += shift_time_in_hours
    else:
      user_on_call_hours[user_pk] = {
        "email": final_shift["user_email"],
        "hours_on_call": shift_time_in_hours,
      }

with open(OUTPUT_FILE_NAME, "w") as fp:
  csv_writer = csv.DictWriter(fp, ["user_pk", "user_email", "hours_on_call"])
  csv_writer.writeheader()

  for user_pk, user_info in user_on_call_hours.items():
    csv_writer.writerow({
      "user_pk": user_pk, "user_email": user_info["email"], "hours_on_call": user_info["hours_on_call"]})
```
