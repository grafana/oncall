---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/personal_notification_rules/
title: Personal notification rules HTTP API
weight: 800
---

# Personal notification rules HTTP API

## Post a personal notification rule

```shell
curl "{{API_URL}}/api/v1/personal_notification_rules/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "user_id": "U4DNY931HHJS5",
      "type": "notify_by_sms"
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "NT79GA9I7E4DJ",
  "user_id": "U4DNY931HHJS5",
  "position": 0,
  "important": false,
  "type": "notify_by_sms"
}
```

| Parameter   | Required | Description                                                                                                                                                                                                                                                                                         |
| ----------- | :------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `user_id`   |   Yes    | User ID                                                                                                                                                                                                                                                                                             |
| `position`  | Optional | Personal notification rules execute one after another starting from `position=0`. `Position=-1` will put the escalation policy to the end of the list. A new escalation policy created with a position of an existing escalation policy will move the old one (and all following) down on the list. |
| `type`      |   Yes    | One of: `wait`, `notify_by_slack`, `notify_by_sms`, `notify_by_phone_call`, `notify_by_telegram`, `notify_by_email`.                                                                                                                                                                                |
| `duration`  | Optional | A time in secs when type `wait` is chosen for `type`.                                                                                                                                                                                                                                               |
| `important` | Optional | Boolean value indicates if a rule is "important". Default is `false`.                                                                                                                                                                                                                               |

**HTTP request**

`POST {{API_URL}}/api/v1/personal_notification_rules/`

## Get personal notification rule

```shell
curl "{{API_URL}}/api/v1/personal_notification_rules/ND9EHN5LN1DUU/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "id": "ND9EHN5LN1DUU",
  "user_id": "U4DNY931HHJS5",
  "position": 1,
  "duration": 300,
  "important": false,
  "type": "wait"
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/personal_notification_rules/<PERSONAL_NOTIFICATION_RULE_ID>/`

## List personal notification rules

```shell
curl "{{API_URL}}/api/v1/personal_notification_rules/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following ways:

```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "NT79GA9I7E4DJ",
      "user_id": "U4DNY931HHJS5",
      "position": 0,
      "important": false,
      "type": "notify_by_sms"
    },
    {
      "id": "ND9EHN5LN1DUU",
      "user_id": "U4DNY931HHJS5",
      "position": 1,
      "duration": 300,
      "important": false,
      "type": "wait"
    },
    {
      "id": "NEF49YQ1HNPDD",
      "user_id": "U4DNY931HHJS5",
      "position": 2,
      "important": false,
      "type": "notify_by_phone_call"
    },
    {
      "id": "NWAL6WFJNWDD8",
      "user_id": "U4DNY931HHJS5",
      "position": 0,
      "important": true,
      "type": "notify_by_phone_call"
    }
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
}
```

The following available filter parameters should be provided as `GET` arguments:

- `user_id`
- `important`

**HTTP Request**

`GET {{API_URL}}/api/v1/personal_notification_rules/`

## Delete a personal notification rule

```shell
curl "{{API_URL}}/api/v1/personal_notification_rules/NWAL6WFJNWDD8/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

**HTTP request**

`DELETE {{API_URL}}/api/v1/personal_notification_rules/<PERSONAL_NOTIFICATION_RULE_ID>/`
