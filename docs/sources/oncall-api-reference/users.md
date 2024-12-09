---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/users/
title: Grafana OnCall users HTTP API
weight: 0
refs:
  pagination:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/oncall-api-reference/#pagination
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/#pagination
---

# Grafana OnCall users HTTP API

## Get a user

**Required permission**: `grafana-oncall-app.user-settings:read`

This endpoint retrieves the user object.

```shell
curl "{{API_URL}}/api/v1/users/current/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
````

The above command returns JSON structured in the following way:

```json
{
  "id": "U4DNY931HHJS5",
  "grafana_id": 456,
  "email": "public-api-demo-user-1@grafana.com",
  "slack": [
    {
      "user_id": "UALEXSLACKDJPK",
      "team_id": "TALEXSLACKDJPK"
    }
  ],
  "username": "alex",
  "role": "admin",
  "timezone": "UTC",
  "teams": []
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/users/<USER_ID>/`

Use `{{API_URL}}/api/v1/users/current` to retrieve the current user.

| Parameter         | Unique  | Description                                                        |
| ----------------- | :-----: | :----------------------------------------------------------------- |
| `id`              | Yes/org | OnCall user ID                                                     |
| `grafana_id`      | Yes/org | Grafana user ID                                                    |
| `email`           | Yes/org | User e-mail                                                        |
| `slack`           | Yes/org | List of user IDs from connected Slack. User linking key is e-mail. |
| `username`        | Yes/org | User username                                                      |
| `role`            |   No    | One of: `user`, `observer`, `admin`.                               |
| `timezone`        |   No    | timezone of the user one of [time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).                               |
| `teams`           |   No    | List of team IDs the user belongs to                               |

## List Users

**Required permission**: `grafana-oncall-app.user-settings:read`

```shell
curl "{{API_URL}}/api/v1/users/" \
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
      "id": "U4DNY931HHJS5",
      "grafana_id": 456,
      "email": "public-api-demo-user-1@grafana.com",
      "slack": [
        {
          "user_id": "UALEXSLACKDJPK",
          "team_id": "TALEXSLACKDJPK"
        }
      ],
      "username": "alex",
      "role": "admin",
      "timezone": "UTC",
      "teams": ["TAAM1K1NNEHAG"]
    }
  ],
  "current_page_number": 1,
  "page_size": 100,
  "total_pages": 1
}
```

> **Note**: The response is [paginated](ref:pagination). You may need to make multiple requests to get all records.

The following available filter parameter should be provided as a `GET` argument:

- `username` (Exact match)

**HTTP request**

`GET {{API_URL}}/api/v1/users/`
