---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/user_groups/
title: OnCall user groups HTTP API
weight: 0
refs:
  pagination:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/oncall-api-reference/#pagination
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/#pagination
---

<!--Used in escalation policies with type = `notify_user_group` and in schedules.-->

# OnCall user groups HTTP API

## List user groups

**Required permission**: `grafana-oncall-app.chatops:read`

```shell
curl "{{API_URL}}/api/v1/user_groups/" \
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
      "id": "GPFAPH7J7BKJB",
      "type": "slack_based",
      "slack": {
        "id": "MEOW_SLACK_ID",
        "name": "Meow Group",
        "handle": "meow_group"
      }
    }
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
}
```

> **Note**: The response is [paginated](ref:pagination). You may need to make multiple requests to get all records.

| Parameter | Unique | Description                                                                                           |
| --------- | :----: | :---------------------------------------------------------------------------------------------------- |
| `id`      |  Yes   | User Group ID                                                                                         |
| `type`    |   No   | [Slack-defined user groups](https://slack.com/intl/en-ru/help/articles/212906697-Create-a-user-group) |
| `slack`   |   No   | Metadata retrieved from Slack.                                                                        |

**HTTP request**

`GET {{API_URL}}/api/v1/user_groups/`
