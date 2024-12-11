---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/alerts/
title: Alerts HTTP API
weight: 0
refs:
  pagination:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/oncall-api-reference/#pagination
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/#pagination
---

# Alerts HTTP API

## List Alerts

**Required permission**: `grafana-oncall-app.alert-groups:read`

```shell
curl "{{API_URL}}/api/v1/alerts/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "AA74DN7T4JQB6",
      "alert_group_id": "I68T24C13IFW1",
      "created_at": "2020-05-11T20:08:43Z",
      "payload": {
        "state": "alerting",
        "title": "[Alerting] Test notification",
        "ruleId": 0,
        "message": "Someone is testing the alert notification within Grafana.",
        "ruleUrl": "{{API_URL}}/",
        "ruleName": "Test notification",
        "evalMatches": [
          {
            "tags": null,
            "value": 100,
            "metric": "High value"
          },
          {
            "tags": null,
            "value": 200,
            "metric": "Higher Value"
          }
        ]
      }
    },
    {
      "id": "AR9SSYFKE2PV7",
      "alert_group_id": "I68T24C13IFW1",
      "created_at": "2020-05-11T20:07:54Z",
      "payload": {
        "state": "alerting",
        "title": "[Alerting] Test notification",
        "ruleId": 0,
        "message": "Someone is testing the alert notification within Grafana.",
        "ruleUrl": "{{API_URL}}/",
        "ruleName": "Test notification",
        "evalMatches": [
          {
            "tags": null,
            "value": 100,
            "metric": "High value"
          },
          {
            "tags": null,
            "value": 200,
            "metric": "Higher Value"
          }
        ]
      }
    },
    {
      "id": "AWJQSGEYYUFGH",
      "alert_group_id": "I68T24C13IFW1",
      "created_at": "2020-05-11T20:06:58Z",
      "payload": {
        "state": "alerting",
        "title": "[Alerting] Test notification",
        "ruleId": 0,
        "message": "Someone is testing the alert notification within Grafana.",
        "ruleUrl": "{{API_URL}}/",
        "ruleName": "Test notification",
        "evalMatches": [
          {
            "tags": null,
            "value": 100,
            "metric": "High value"
          },
          {
            "tags": null,
            "value": 200,
            "metric": "Higher Value"
          }
        ]
      }
    }
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
}
```

> **Note**: The response is [paginated](ref:pagination). You may need to make multiple requests to get all records.

The following available filter parameters should be provided as `GET` arguments:

- `id`
- `alert_group_id`
- `search`—string-based inclusion search by alert payload

**HTTP request**

`GET {{API_URL}}/api/v1/alerts/`
