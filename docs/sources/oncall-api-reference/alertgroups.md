---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/alertgroups/
title: Alert groups HTTP API
weight: 400
---

# List alert groups

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
      "title": "Memory above 90% threshold",
      "permalinks": {
        "slack": "https://ghostbusters.slack.com/archives/C1H9RESGA/p135854651500008",
        "telegram": "https://t.me/c/5354/1234?thread=1234"
      }
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

# Delete alert groups

```shell
curl "{{API_URL}}/api/v1/alert_groups/I68T24C13IFW1/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "mode": "wipe"
  }'
```

| Parameter | Required | Description                                                                                                                                                                                                                                                                                                                                      |
| --------- | :------: | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mode`    |    No    | Default setting is `wipe`. `wipe` will remove the payload of all Grafana OnCall group alerts. This is useful if you sent sensitive data to OnCall. All metadata will remain. `DELETE` will trigger the removal of alert groups, alerts, and all related metadata. It will also remove alert group notifications in Slack and other destinations. |

> **NOTE:** `DELETE` can take a few moments to delete alert groups because Grafana OnCall interacts with 3rd party APIs
> such as Slack. Please check objects using `GET` to be sure the data is removed.

**HTTP request**

`DELETE {{API_URL}}/api/v1/alert_groups/<ALERT_GROUP_ID>`
