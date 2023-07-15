---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/outgoing_webhooks/
title: Outgoing webhooks HTTP API
weight: 700
---

# Outgoing webhooks (actions)

⚠️ NOTE: these endpoints are now read-only/deprecated and will be removed in the near future, once public API support
for Outgoing Webhooks v2 is released. See the docs [here][outgoing-webhooks-v2-docs] for more information on Outgoing
Webhooks v2. ⚠️

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

{{% docs/reference %}}
[outgoing-webhooks-v2-docs]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/outgoing-webhooks"
[outgoing-webhooks-v2-docs]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/outgoing-webhooks"
{{% /docs/reference %}}
