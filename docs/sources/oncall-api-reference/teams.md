---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/teams/
title: Grafana OnCall teams HTTP API
weight: 0
refs:
  pagination:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/oncall-api-reference/#pagination
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/#pagination
---

# Grafana OnCall teams HTTP API

## Get a team

**Required permission**: `grafana-oncall-app.user-settings:read`

This endpoint retrieves the team object.

```shell
curl "{{API_URL}}/api/v1/teams/TI73TDU19W48J/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
````

The above command returns JSON structured in the following way:

```json
{
  "id": "TI73TDU19W48J",
  "grafana_id": 123,
  "name": "my test team",
  "email": "",
  "avatar_url": "/avatar/3f49c15916554246daa714b9bd0ee398"
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/teams/<TEAM_ID>/`

| Parameter         | Unique  | Description                    |
| ----------------- | :-----: | :----------------------------- |
| `id`              | Yes/org | OnCall team ID                 |
| `grafana_id`      | Yes/org | Grafana team ID                |
| `name`            | Yes/org | Team name                      |
| `email`           | Yes/org | Team e-mail                    |
| `avatar_url`      | Yes     | Avatar URL of the Grafana team |

## List Teams

**Required permission**: `grafana-oncall-app.user-settings:read`

```shell
curl "{{API_URL}}/api/v1/teams/" \
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
      "id": "TI73TDU19W48J",
      "grafana_id": 123,
      "name": "my test team",
      "email": "",
      "avatar_url": "/avatar/3f49c15916554246daa714b9bd0ee398"
    }
  ],
  "page_size": 50,
  "current_page_number": 1,
  "total_pages": 1
}
```

> **Note**: The response is [paginated](ref:pagination). You may need to make multiple requests to get all records.

The following available filter parameter should be provided as a `GET` argument:

- `name` (Exact match)

**HTTP request**

`GET {{API_URL}}/api/v1/teams/`
