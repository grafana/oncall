---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/direct_paging/
title: Direct paging HTTP API
weight: 1200
refs:
  users:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/oncall-api-reference/users
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/users
  teams:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/oncall-api-reference/teams
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/teams
---

# Direct paging HTTP API

## Directly page a set of users

For more details about how to fetch a user's Grafana OnCall ID, refer to the [Users](ref:users) public API documentation.

```shell
curl "{{API_URL}}/api/v1/direct_paging/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
    "title": "We are seeing a network outage in the datacenter",
    "message": "I need help investigating, can you join the investigation?",
    "source_url": "https://github.com/myorg/myrepo/issues/123",
    "users": [
      {
        "id": "U281SN24AVVJX",
        "important": false
      },
      {
        "id": "U5AKCVNDEDUE7",
        "important": true
      }
    ]
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "alert_group_id": "IZHCC4GTNPZ93"
}
```

## Directly page a team

For more details about how to fetch a team's Grafana OnCall ID, refer to the [Teams](ref:teams) public API documentation.

```shell
curl "{{API_URL}}/api/v1/direct_paging/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
    "title": "We are seeing a network outage in the datacenter",
    "message": "I need help investigating, can you join the investigation?",
    "source_url": "https://github.com/myorg/myrepo/issues/123",
    "team": "TI73TDU19W48J"
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "alert_group_id": "IZHCC4GTNPZ93"
}
```

## Directly page user(s) for an existing Alert Group

The following shows how you can directly page user(s) for an existing Alert Group.

```shell
curl "{{API_URL}}/api/v1/direct_paging/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
    "alert_group_id": "IZMRNNY8RFS94",
    "users": [
      {
        "id": "U281SN24AVVJX",
        "important": false
      },
      {
        "id": "U5AKCVNDEDUE7",
        "important": true
      }
    ]
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "alert_group_id": "IZMRNNY8RFS94"
}
```

| Parameter            | Unique |     Required     | Description                                                                                                                                                                                                                                         |
| -------------------- | :----: | :--------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`               |  No   |       No        | Name of the Alert Group that will be created                                                                                                                                                                                                                                      |
| `message`               |  No   |       No        | Content of the Alert Group that will be created                                                                                                                                                                                       |
| `source_url`               |  No   |       No        | Value that will be added in the Alert's payload as `oncall.permalink`. This can be useful to have the source URL/button autopopulated with a URL of interest.                        |
| `team`               |  No   |       Yes (see [Things to Note](#things-to-note))        | Grafana OnCall team ID. If specified, will use the Direct Paging Integration associated with this Grafana OnCall team, to create the Direct Paging Alert Group.                                                                                                                                                                                        |
| `users`               |  No   |       Yes (see [Things to Note](#things-to-note))        | List of user(s) to Direct Page. See above request example for object schema. `id` represents the Grafana OnCall user's ID. `important` is a boolean representing whether to escalate the Alert Group using this user's default or important personal notification policy.                                                                                                                                                                                        |
| `alert_group_id`               |  No   |       No        | If specified, will directly page the specified users for this Alert Group.                                                                                                                                                                                         |

## Things to note

- `team` and `users` are mutually exclusive in the request payload. If you would like to directly page a team AND user(s),
first directly page a team, then using the Alert Group ID returned in response payload, add the required users to the
existing Alert Group
- `alert_group_id` is mutually exclusive with `title`, `message`, and `source_url`. Practically speaking this means that
if you are trying to directly page users on an existing Alert Group, you cannot update the `title`, `message`, or
`source_url` of that Alert Group
- If directly paging users for an existing Alert Group, the Alert Group cannot be in a resolved state

**HTTP request**

`POST {{API_URL}}/api/v1/direct_paging/`
