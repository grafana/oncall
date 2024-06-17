---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/users/
title: Grafana OnCall users HTTP API
weight: 1500
---

# Grafana OnCall users HTTP API

## Get a user

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

| Parameter  | Unique  | Description                                                        |
| ---------- | :-----: | :----------------------------------------------------------------- |
| `id`       | Yes/org | User ID                                                            |
| `email`    | Yes/org | User e-mail                                                        |
| `slack`    | Yes/org | List of user IDs from connected Slack. User linking key is e-mail. |
| `username` | Yes/org | User username                                                      |
| `role`     |   No    | One of: `user`, `observer`, `admin`.                               |
| `timezone` |   No    | timezone of the user one of [time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).                               |
| `teams`    |   No    | List of team IDs the user belongs to                               |

## List Users

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

This endpoint retrieves all users.

The following available filter parameter should be provided as a `GET` argument:

- `username` (Exact match)

**HTTP request**

`GET {{API_URL}}/api/v1/users/`
