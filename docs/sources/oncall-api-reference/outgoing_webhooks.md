---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/outgoing_webhooks/
title: Outgoing webhooks HTTP API
weight: 700
---

# Outgoing webhooks (actions)

Used in escalation policies with type `trigger_action`.

## List actions

```shell
curl "{{API_URL}}/api/v1/actions/" \
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
      "id": "KGEFG74LU1D8L",
      "name": "Publish alert group notification to JIRA"
    }
  ]
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/actions/`
