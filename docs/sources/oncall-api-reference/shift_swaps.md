---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/shift_swaps/
title: Shift swap requests HTTP API
weight: 1200
---

# Shift swap requests HTTP API

## Create a shift swap request

```shell
curl "{{API_URL}}/api/v1/shift_swaps/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
        "schedule": "SRJWJCMKD68AL",
        "swap_start": "2026-06-11T00:00:00Z",
        "swap_end": "2026-07-19T22:00:00Z",
        "description": "Anyone to cover my shifts?",
        "beneficiary": "UWJWIN8MQ1GYL"
  }'
```

The above command returns JSON structured in the following way:

```json
{
   "benefactor" : null,
   "beneficiary" : "UWJWIN8MQ1GYL",
   "created_at" : "2023-08-11T19:20:17.064677Z",
   "description" : "Anyone to cover my shifts?",
   "id" : "SSRG1TDNBMJQ1NC",
   "schedule" : "SRJWJCMKD68AL",
   "shifts" : [
      {
         "all_day" : false,
         "calendar_type" : 0,
         "end" : "2026-06-11T03:00:00Z",
         "is_empty" : false,
         "is_gap" : false,
         "is_override" : false,
         "missing_users" : [],
         "priority_level" : 2,
         "shift" : {
            "pk" : "OTI13GNNE5V1L"
         },
         "source" : "web",
         "start" : "2026-06-11T00:00:00Z",
         "users" : [
            {
               "avatar_full" : "http://avatar.url",
               "display_name" : "testing",
               "email" : "testing",
               "pk" : "UWJWIN8MQ1GYL",
               "swap_request" : {
                  "pk" : "SSRG1TDNBMJQ1NC"
               }
            }
         ]
      }
   ],
   "status" : "open",
   "swap_end" : "2026-07-19T22:00:00.000000Z",
   "swap_start" : "2026-06-11T00:00:00.000000Z",
   "updated_at" : "2023-08-11T19:20:17.064922Z"
}
```

| Parameter            | Unique |     Required     | Description                                                                                                                                                                                                                                         |
| -------------------- | :----: | :--------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `schedule`               |  No   |       Yes        | ID of the schedule.                                                                                                                                                                                                                                      |
| `swap_start`               |   No   |       Yes        | Start date/time for the swap request. Must be a ISO 8601 formatted datetime string.                                                                                                                             |
| `swap_end`            |   No   |        No        | End date/time for the swap request. Must be a ISO 8601 formatted datetime string.                                                                                                                                                                                                                                     |
| `description`          |   No   |     Optional     | A description message to be displayed along the request. |
| `beneficiary`   |   No   | Yes | ID of the user requesting the swap.                                                                                                                                                                                        |

**HTTP request**

`POST {{API_URL}}/api/v1/shift_swaps/`

## Get a shift swap request

```shell
curl "{{API_URL}}/api/v1/shift_swaps/SSRG1TDNBMJQ1NC/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
   "benefactor" : null,
   "beneficiary" : "UWJWIN8MQ1GYL",
   "created_at" : "2023-08-11T19:20:17.064677Z",
   "description" : "Anyone to cover my shifts?",
   "id" : "SSRG1TDNBMJQ1NC",
   "schedule" : "SRJWJCMKD68AL",
   "shifts" : [
      {
         "all_day" : false,
         "calendar_type" : 0,
         "end" : "2026-06-11T03:00:00Z",
         "is_empty" : false,
         "is_gap" : false,
         "is_override" : false,
         "missing_users" : [],
         "priority_level" : 2,
         "shift" : {
            "pk" : "OTI13GNNE5V1L"
         },
         "source" : "web",
         "start" : "2026-06-11T00:00:00Z",
         "users" : [
            {
               "avatar_full" : "http://avatar.url",
               "display_name" : "testing",
               "email" : "testing",
               "pk" : "UWJWIN8MQ1GYL",
               "swap_request" : {
                  "pk" : "SSRG1TDNBMJQ1NC"
               }
            }
         ]
      }
   ],
   "status" : "open",
   "swap_end" : "2026-07-19T22:00:00.000000Z",
   "swap_start" : "2026-06-11T00:00:00.000000Z",
   "updated_at" : "2023-08-11T19:20:17.064922Z"
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/shift_swaps/<SHIFT_SWAP_REQUEST_ID>/`

## List shift swap requests

```shell
curl "{{API_URL}}/api/v1/shift_swaps/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
   "count" : 2,
   "current_page_number" : 1,
   "next" : null,
   "page_size" : 50,
   "previous" : null,
   "results" : [
      {
         "benefactor" : "UWJWIN8MQ1GYL",
         "beneficiary" : "UCGEIXI1MR1NZ",
         "created_at" : "2023-08-07T18:44:15.249679Z",
         "description" : "Taking a few days off.",
         "id" : "SSRK2EH2TR6E4F9",
         "schedule" : "SRZZFY1QI9FLL",
         "status" : "taken",
         "swap_end" : "2024-09-29T03:00:18.000000Z",
         "swap_start" : "2024-09-26T03:00:18.000000Z",
         "updated_at" : "2024-08-07T18:44:15.249960Z"
      },
      {
         "benefactor" : null,
         "beneficiary" : "UWJWIN8MQ1GYL",
         "created_at" : "2023-08-11T19:20:17.064677Z",
         "description" : "Anyone to cover my shifts?",
         "id" : "SSRG1TDNBMJQ1NC",
         "schedule" : "SRJWJCMKD68AL",
         "status" : "open",
         "swap_end" : "2026-07-19T22:00:00.000000Z",
         "swap_start" : "2026-06-11T00:00:00.000000Z",
         "updated_at" : "2023-08-11T19:20:17.064922Z"
      }
   ],
   "total_pages" : 1
}
```

The following available filter parameters may be provided as a `GET` arguments:

- `starting_after` (an ISO 8601 timestamp string, filter requests starting after the specified datetime)
- `schedule_id` (Exact match, schedule ID)
- `beneficiary` (Exact match, user ID)
- `benefactor` (Exact match, user ID)
- `open_only` (set to `true` to filter active untaken requests only)

**HTTP request**

`GET {{API_URL}}/api/v1/shift_swaps/`

## Update a shift swap request

```shell
curl "{{API_URL}}/api/v1/shift_swaps/SSRG1TDNBMJQ1NC/" \
  --request PUT \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
        "schedule": "SRJWJCMKD68AL",
        "swap_start": "2026-06-11T00:00:00Z",
        "swap_end": "2026-07-20T22:00:00Z"
  }'
```

The above command returns JSON structured in the following way:

```json
{
   "benefactor" : null,
   "beneficiary" : "UWJWIN8MQ1GYL",
   "created_at" : "2023-08-11T19:20:17.064677Z",
   "description" : "Anyone to cover my shifts?",
   "id" : "SSRG1TDNBMJQ1NC",
   "schedule" : "SRJWJCMKD68AL",
   "shifts" : [
      {
         "all_day" : false,
         "calendar_type" : 0,
         "end" : "2026-06-11T03:00:00Z",
         "is_empty" : false,
         "is_gap" : false,
         "is_override" : false,
         "missing_users" : [],
         "priority_level" : 2,
         "shift" : {
            "pk" : "OTI13GNNE5V1L"
         },
         "source" : "web",
         "start" : "2026-06-11T00:00:00Z",
         "users" : [
            {
               "avatar_full" : "http://avatar.url",
               "display_name" : "testing",
               "email" : "testing",
               "pk" : "UWJWIN8MQ1GYL",
               "swap_request" : {
                  "pk" : "SSRG1TDNBMJQ1NC"
               }
            }
         ]
      }
   ],
   "status" : "open",
   "swap_end" : "2026-07-20T22:00:00.000000Z",
   "swap_start" : "2026-06-11T00:00:00.000000Z",
   "updated_at" : "2023-08-11T19:45:53.096811Z"
}

```

**HTTP request**

`PUT {{API_URL}}/api/v1/shift_swaps/<SHIFT_SWAP_REQUEST_ID>/`

## Delete a shift swap request

```shell
curl "{{API_URL}}/api/v1/shift_swaps/SSRG1TDNBMJQ1NC/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

**HTTP request**

`DELETE {{API_URL}}/api/v1/shift_swaps/<SHIFT_SWAP_REQUEST_ID>/`

## Take a shift swap request

```shell
curl "{{API_URL}}/api/v1/shift_swaps/SSRG1TDNBMJQ1NC/take" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
        "benefactor": "UCGEIXI1MR1NZ"
  }'
```

The above command returns JSON structured in the following way:

```json
{
   "benefactor" : "UCGEIXI1MR1NZ",
   "beneficiary" : "UWJWIN8MQ1GYL",
   "created_at" : "2023-08-11T19:20:17.064677Z",
   "description" : "Anyone to cover my shifts?",
   "id" : "SSRG1TDNBMJQ1NC",
   "schedule" : "SRJWJCMKD68AL",
   "shifts" : [
      {
         "all_day" : false,
         "calendar_type" : 0,
         "end" : "2026-06-11T03:00:00Z",
         "is_empty" : false,
         "is_gap" : false,
         "is_override" : false,
         "missing_users" : [],
         "priority_level" : 2,
         "shift" : {
            "pk" : "OTI13GNNE5V1L"
         },
         "source" : "web",
         "start" : "2026-06-11T00:00:00Z",
         "users" : [
            {
               "avatar_full" : "http://avatar.url",
               "display_name" : "anotherone",
               "email" : "anotherone",
               "pk" : "UCGEIXI1MR1NZ",
               "swap_request" : {
                  "pk" : "SSRG1TDNBMJQ1NC",
                  "user" : {
                     "avatar_full" : "http://avatar.url",
                     "display_name" : "testing",
                     "email" : "testing",
                     "pk" : "UWJWIN8MQ1GYL"
                  }
               }
            }
         ]
      }
   ],
   "status" : "taken",
   "swap_end" : "2026-07-20T22:00:00.000000Z",
   "swap_start" : "2026-06-11T00:00:00.000000Z",
   "updated_at" : "2023-08-11T19:51:38.622037Z"
}
```

| Parameter            | Unique |     Required     | Description                                                                                                                                                                                                                                         |
| -------------------- | :----: | :--------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `benefactor`   |   No   | Yes | ID of the user taking the swap.                                                                                                                                                                                        |

**HTTP request**

`POST {{API_URL}}/api/v1/shift_swaps/<SHIFT_SWAP_REQUEST_ID>/take`
