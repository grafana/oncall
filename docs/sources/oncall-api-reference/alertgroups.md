---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/alertgroups/
title: Alert groups HTTP API
weight: 400
---

# Alert groups HTTP API

## List alert groups

```shell
curl "{{API_URL}}/api/v1/alert_groups/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "I68T24C13IFW1",
      "integration_id": "CFRPV98RPR1U8",
      "route_id": "RIYGUJXCPFHXY",
      "alerts_count": 3,
      "state": "resolved",
      "created_at": "2020-05-19T12:37:01.430444Z",
      "resolved_at": "2020-05-19T13:37:01.429805Z",
      "acknowledged_at": null,
      "acknowledged_by": null,
      "resolved_by": "UCGEIXI1MR1NZ",
      "title": "Memory above 90% threshold",
      "permalinks": {
        "slack": "https://ghostbusters.slack.com/archives/C1H9RESGA/p135854651500008",
        "telegram": "https://t.me/c/5354/1234?thread=1234"
      },
      "silenced_at": "2020-05-19T13:37:01.429805Z",
    }
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
}
```

These available filter parameters should be provided as `GET` arguments:

- `id`
- `route_id`
- `integration_id`
- `state`

**HTTP request**

`GET {{API_URL}}/api/v1/alert_groups/`

## Alert group details

```shell
curl "{{API_URL}}/api/v1/alert_groups/I68T24C13IFW1" \
  --request GET \
  --header "Authorization: meowmeowmeow"
```

**HTTP request**

`GET {{API_URL}}/api/v1/alert_groups/<ALERT_GROUP_ID>`

## Acknowledge an alert group

```shell
curl "{{API_URL}}/api/v1/alert_groups/I68T24C13IFW1/acknowledge" \
  --request POST \
  --header "Authorization: meowmeowmeow"
```

**HTTP request**

`POST {{API_URL}}/api/v1/alert_groups/<ALERT_GROUP_ID>/acknowledge`

## Unacknowledge an alert group

```shell
curl "{{API_URL}}/api/v1/alert_groups/I68T24C13IFW1/unacknowledge" \
  --request POST \
  --header "Authorization: meowmeowmeow"
```

**HTTP request**

`POST {{API_URL}}/api/v1/alert_groups/<ALERT_GROUP_ID>/unacknowledge`

## Resolve an alert group

```shell
curl "{{API_URL}}/api/v1/alert_groups/I68T24C13IFW1/resolve" \
  --request POST \
  --header "Authorization: meowmeowmeow"
```

**HTTP request**

`POST {{API_URL}}/api/v1/alert_groups/<ALERT_GROUP_ID>/resolve`

## Unresolve an alert group

```shell
curl "{{API_URL}}/api/v1/alert_groups/I68T24C13IFW1/unresolve" \
  --request POST \
  --header "Authorization: meowmeowmeow"
```

**HTTP request**

`POST {{API_URL}}/api/v1/alert_groups/<ALERT_GROUP_ID>/unresolve`

## Delete an alert group

```shell
curl "{{API_URL}}/api/v1/alert_groups/I68T24C13IFW1/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "mode": "wipe"
  }'
```

| Parameter | Required | Description                                                                                                                                                                                                                                                                                                                                             |
|-----------|:--------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `mode`    |    No    | The default value for this parameter is `wipe`. Using `wipe` will delete the content of the alert group but keep the metadata, which is helpful if you've sent sensitive information to OnCall. On the other hand, passing `delete` will fully erase the alert group and its metadata, as well as delete related messages in Slack and other platforms. |

> **NOTE:** `DELETE` can take a few moments to delete alert groups because Grafana OnCall interacts with 3rd party APIs
> such as Slack. Please check objects using `GET` to be sure the data is removed.

**HTTP request**

`DELETE {{API_URL}}/api/v1/alert_groups/<ALERT_GROUP_ID>`
