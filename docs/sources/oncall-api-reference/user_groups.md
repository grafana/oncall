---
aliases:
  - /docs/oncall/latest/oncall-api-reference/user_groups/
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/user_groups/
title: User groups HTTP API
weight: 1400
---

# User groups HTTP API

<!--Used in escalation policies with type = `notify_user_group` and in schedules.-->

## List user groups

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
  ]
}
```

<!-- markdownlint-disable MD013 -->

| Parameter | Unique | Description                                                                                           |
| --------- | :----: | :---------------------------------------------------------------------------------------------------- |
| `id`      |  Yes   | User Group ID                                                                                         |
| `type`    |   No   | [Slack-defined user groups](https://slack.com/intl/en-ru/help/articles/212906697-Create-a-user-group) |
| `slack`   |   No   | Metadata retrieved from Slack.                                                                        |

<!-- markdownlint-enable MD013 -->

**HTTP request**

`GET {{API_URL}}/api/v1/user_groups/`
