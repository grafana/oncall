---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/on_call_shifts/
title: OnCall shifts HTTP API
weight: 600
---

# OnCall shifts HTTP API

## Create an OnCall shift

```shell
curl "{{API_URL}}/api/v1/on_call_shifts/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "name": "Demo single event",
      "type": "single_event",
      "team_id": null,
      "time_zone": null,
      "level": 0,
      "start": "2020-09-10T08:00:00",
      "duration": 10800,
      "users": [
          "U4DNY931HHJS5"
      ]
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "OH3V5FYQEYJ6M",
  "name": "Demo single event",
  "type": "single_event",
  "team_id": null,
  "time_zone": null,
  "level": 0,
  "start": "2020-09-10T08:00:00",
  "duration": 10800,
  "users": ["U4DNY931HHJS5"]
}
```

| Parameter                        | Unique |                    Required                    | Description                                                                                                                                                                                                                                                                                                                                                                                                        |
| -------------------------------- | :----: | :--------------------------------------------: | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                           |  Yes   |                      Yes                       | On-call shift name.                                                                                                                                                                                                                                                                                                                                                                                                |
| `type`                           |   No   |                      Yes                       | One of: `single_event`, `recurrent_event`, `rolling_users`.                                                                                                                                                                                                                                                                                                                                                        |
| `team_id`                        |   No   |                ID of the team.                 |
| `time_zone`                      |   No   |                    Optional                    | On-call shift time zone. Default is local schedule time zone. **This field will override the schedule time zone if changed**. For more information refer to [time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).                                                                                                                                                                                 |
| `level`                          |   No   |                    Optional                    | Priority level. The higher the value, the higher the priority. If two events overlap in one schedule, Grafana OnCall will choose the event with higher level. For example: Alex is on-call from 8AM till 11AM with level 1, Bob is on-call from 9AM till 11AM with level 2. At 10AM Grafana OnCall will notify Bob. At 8AM OnCall will notify Alex.                                                                |
| `start`                          |   No   |                      Yes                       | Start time of the on-call shift. This parameter takes a date format as `yyyy-MM-dd'T'HH:mm:ss` (for example "2020-09-05T08:00:00").                                                                                                                                                                                                                                                                                |
| `duration`                       |   No   |                      Yes                       | Duration of the event.                                                                                                                                                                                                                                                                                                                                                                                             |
| `frequency`                      |   No   | If type = `recurrent_event` or `rolling_users` | One of: `hourly`, `daily`, `weekly`, `monthly`.                                                                                                                                                                                                                                                                                                                                                                    |
| `interval`                       |   No   |                    Optional                    | This parameter takes a positive integer that represents the intervals that the recurrence rule repeats. If `frequency` is set, the default assumed value for this will be `1`.                                                                                                                                                                                                                                     |
| `until`                          |   No   |                    Optional                    | When the recurrence rule ends (endless if None). This parameter takes a date format as `yyyy-MM-dd'T'HH:mm:ss` (for example "2020-09-05T08:00:00").                                                                                                                                                                                                                                                                |
| `week_start`                     |   No   |                    Optional                    | Start day of the week in iCal format. One of: `SU` (Sunday), `MO` (Monday), `TU` (Tuesday), `WE` (Wednesday), `TH` (Thursday), `FR` (Friday), `SA` (Saturday). Default: `SU`.                                                                                                                                                                                                                                      |
| `by_day`                         |   No   |                    Optional                    | List of days in iCal format. Valid values are: `SU`, `MO`, `TU`, `WE`, `TH`, `FR`, `SA`.                                                                                                                                                                                                                                                                                                                           |
| `by_month`                       |   No   |                    Optional                    | List of months. Valid values are `1` to `12`.                                                                                                                                                                                                                                                                                                                                                                      |
| `by_monthday`                    |   No   |                    Optional                    | List of days of the month. Valid values are `1` to `31` or `-31` to `-1`.                                                                                                                                                                                                                                                                                                                                          |
| `users`                          |   No   |                    Optional                    | List of on-call users.                                                                                                                                                                                                                                                                                                                                                                                             |
| `rolling_users`                  |   No   |                    Optional                    | List of lists with on-call users (for `rolling_users` event type). Grafana OnCall will iterate over lists of users for every time frame specified in `frequency`. For example: there are two lists of users in `rolling_users` : [[Alex, Bob], [Alice]] and `frequency` = `daily` . This means that the first day Alex and Bob will be notified. The next day: Alice. The day after: Alex and Bob again and so on. |
| `start_rotation_from_user_index` |   No   |                    Optional                    | Index of the list of users in `rolling_users`, from which on-call rotation starts. By default, the start index is `0`                                                                                                                                                                                                                                                                                              |

For more information about recurrence rules, refer to [RFC 5545](https://tools.ietf.org/html/rfc5545#section-3.3.10).

**HTTP request**

`POST {{API_URL}}/api/v1/on_call_shifts/`

## Get OnCall shifts

```shell
curl "{{API_URL}}/api/v1/on_call_shifts/OH3V5FYQEYJ6M/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
```

The above command returns JSON structured in the following way:

```json
{
  "id": "OH3V5FYQEYJ6M",
  "name": "Demo single event",
  "type": "single_event",
  "team_id": null,
  "time_zone": null,
  "level": 0,
  "start": "2020-09-10T08:00:00",
  "duration": 10800,
  "users": ["U4DNY931HHJS5"]
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/on_call_shifts/<ON_CALL_SHIFT_ID>/`

## List OnCall shifts

```shell
curl "{{API_URL}}/api/v1/on_call_shifts/" \
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
      "id": "OH3V5FYQEYJ6M",
      "name": "Demo single event",
      "type": "single_event",
      "team_id": null,
      "time_zone": null,
      "level": 0,
      "start": "2020-09-10T08:00:00",
      "duration": 10800,
      "users": ["U4DNY931HHJS5"]
    },
    {
      "id": "O9WTH7CKM3KZW",
      "name": "Demo recurrent event",
      "type": "recurrent_event",
      "team_id": null,
      "time_zone": null,
      "level": 0,
      "start": "2020-09-10T16:00:00",
      "duration": 10800,
      "frequency": "weekly",
      "interval": 2,
      "week_start": "SU",
      "by_day": ["MO", "WE", "FR"],
      "by_month": null,
      "by_monthday": null,
      "users": ["U4DNY931HHJS5"]
    }
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
}
```

The following available filter parameters should be provided as `GET` arguments:

- `name` (Exact match)
- `schedule_id` (Exact match)

**HTTP request**

`GET {{API_URL}}/api/v1/on_call_shifts/`

## Update OnCall shift

```shell
curl "{{API_URL}}/api/v1/on_call_shifts/OH3V5FYQEYJ6M/" \
  --request PUT \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
    "name": "Demo single event",
    "type": "single_event",
    "level": 0,
    "start": "2020-09-10T08:00:00",
    "duration": 10800,
    "users": [
        "U4DNY931HHJS5"
    ]
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "OH3V5FYQEYJ6M",
  "name": "Demo single event",
  "type": "single_event",
  "team_id": null,
  "time_zone": null,
  "level": 0,
  "start": "2020-09-10T08:00:00",
  "duration": 10800,
  "users": ["U4DNY931HHJS5"]
}
```

**HTTP request**

`PUT {{API_URL}}/api/v1/on_call_shifts/<ON_CALL_SHIFT_ID>/`

## Delete OnCall shift

```shell
curl "{{API_URL}}/api/v1/on_call_shifts/OH3V5FYQEYJ6M/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

**HTTP request**

`DELETE {{API_URL}}/api/v1/on_call_shifts/<ON_CALL_SHIFT_ID>/`
