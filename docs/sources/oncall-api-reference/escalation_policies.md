---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/escalation_policies/
title: Escalation policies HTTP API
weight: 300
---

# Escalation policies HTTP API

## Create an escalation policy

```shell
curl "{{API_URL}}/api/v1/escalation_policies/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "escalation_chain_id": "F5JU6KJET33FE",
      "type": "wait",
      "duration": 60
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "E3GA6SJETWWJS",
  "escalation_chain_id": "F5JU6KJET33FE",
  "position": 0,
  "type": "wait",
  "duration": 60
}
```

| Parameter                          |                 Required                 | Description                                                                                                                                                                                                                                                                                 |
| ---------------------------------- | :--------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `escalation_chain_id`              |                   Yes                    | Each escalation policy is assigned to a specific escalation chain.                                                                                                                                                                                                                          |
| `position`                         |                 Optional                 | Escalation policies execute one after another starting from `position=0`. `Position=-1` will put the escalation policy to the end of the list. A new escalation policy created with a position of an existing escalation policy will move the old one (and all following) down in the list. |
| `type`                             |                   Yes                    | One of: `wait`, `notify_persons`, `notify_person_next_each_time`, `notify_on_call_from_schedule`, `notify_user_group`, `trigger_webhook`, `resolve`, `notify_whole_channel`, `notify_if_time_from_to`.                                                                                       |
| `important`                        |                 Optional                 | Default is `false`. Will assign "important" to personal notification rules if `true`. This can be used to distinguish alerts on which you want to be notified immediately by phone. Applicable for types `notify_persons`, `notify_team_members`, `notify_on_call_from_schedule`, and `notify_user_group`.         |
| `duration`                         |            If type = `wait`              | The duration, in seconds, when type `wait` is chosen. Valid values are: `60`, `300`, `900`, `1800`, `3600`.                                                                                                                                                                                 |
| `action_to_trigger`                |        If type = `trigger_webhook`        | ID of a webhook.                                                                                                                                                                                                                                                                |
| `group_to_notify`                  |      If type = `notify_user_group`       | ID of a `User Group`.                                                                                                                                                                                                                                                                       |
| `persons_to_notify`                |        If type = `notify_persons`        | List of user IDs.                                                                                                                                                                                                                                                                           |
| `persons_to_notify_next_each_time` | If type = `notify_person_next_each_time` | List of user IDs.                                                                                                                                                                                                                                                                           |
| `notify_on_call _from_schedule`    | If type = `notify_on_call_from_schedule` | ID of a Schedule.                                                                                                                                                                                                                                                                           |
| `notify_if_time_from`              |    If type = `notify_if_time_from_to`    | UTC time represents the beginning of the time period, for example `09:00:00Z`.                                                                                                                                                                                                              |
| `notify_if_time_to`                |    If type = `notify_if_time_from_to`    | UTC time represents the end of the time period, for example `18:00:00Z`.                                                                                                                                                                                                                    |
| `team_to_notify`                   |        If type = `notify_team_members`        | ID of a team.                                                                                                                                                                                                                                                                           |

**HTTP request**

`POST {{API_URL}}/api/v1/escalation_policies/`

## Get an escalation policy

```shell
curl "{{API_URL}}/api/v1/escalation_policies/E3GA6SJETWWJS/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
```

The above command returns JSON structured in the following way:

```json
{
  "id": "E3GA6SJETWWJS",
  "escalation_chain_id": "F5JU6KJET33FE",
  "position": 0,
  "type": "wait",
  "duration": 60
}
```

## Update an escalation policy

```shell
curl "{{API_URL}}/api/v1/escalation_policies/E3GA6SJETWWJS/" \
  --request PUT \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
    "type": "wait",
    "duration": 300,
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "E3GA6SJETWWJS",
  "escalation_chain_id": "F5JU6KJET33FE",
  "position": 0,
  "type": "wait",
  "duration": 300
}
```

**HTTP request**

`PUT {{API_URL}}/api/v1/on_call_shifts/<ON_CALL_SHIFT_ID>/`

**HTTP request**

`GET {{API_URL}}/api/v1/escalation_policies/<ESCALATION_POLICY_ID>/`

## List escalation policies

```shell
curl "{{API_URL}}/api/v1/escalation_policies/" \
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
      "id": "E3GA6SJETWWJS",
      "escalation_chain_id": "F5JU6KJET33FE",
      "position": 0,
      "type": "wait",
      "duration": 60
    },
    {
      "id": "E5JJTU52M5YM4",
      "escalation_chain_id": "F5JU6KJET33FE",
      "position": 1,
      "type": "notify_person_next_each_time",
      "persons_to_notify_next_each_time": ["U4DNY931HHJS5"]
    }
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
}
```

The following available filter parameter should be provided as a `GET` argument:

- `escalation_chain_id`

**HTTP request**

`GET {{API_URL}}/api/v1/escalation_policies/`

## Delete an escalation policy

```shell
curl "{{API_URL}}/api/v1/escalation_policies/E3GA6SJETWWJS/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

**HTTP request**

`DELETE {{API_URL}}/api/v1/escalation_policies/<ESCALATION_POLICY_ID>/`
