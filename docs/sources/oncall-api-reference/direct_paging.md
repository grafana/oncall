---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/direct_paging/
title: Direct paging HTTP API
weight: 1200
---

# Direct paging HTTP API

## Directly page a team or user(s)

```shell
curl "{{API_URL}}/api/v1/direct_paging/" \
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

`POST {{API_URL}}/api/v1/direct_paging/`
