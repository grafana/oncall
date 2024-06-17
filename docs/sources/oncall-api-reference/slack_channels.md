---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/slack_channels/
title: Slack channels HTTP API
weight: 1300
---

# Slack channels HTTP API

## List Slack Channels

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

The following available filter parameter should be provided as a `GET` argument:

- `channel_name`

**HTTP Request**

`GET {{API_URL}}/api/v1/slack_channels/`
