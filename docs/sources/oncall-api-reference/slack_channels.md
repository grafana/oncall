---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/slack_channels/
title: Slack channels HTTP API
weight: 0
refs:
  pagination:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/oncall-api-reference/#pagination
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/#pagination
---

# Slack channels HTTP API

## List Slack Channels

**Required permission**: `grafana-oncall-app.chatops:read`

```shell
curl "{{API_URL}}/api/v1/slack_channels/" \
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
      "name": "meow_channel",
      "slack_id": "MEOW_SLACK_ID"
    }
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
}
```

> **Note**: The response is [paginated](ref:pagination). You may need to make multiple requests to get all records.

The following available filter parameter should be provided as a `GET` argument:

- `channel_name`

**HTTP Request**

`GET {{API_URL}}/api/v1/slack_channels/`
