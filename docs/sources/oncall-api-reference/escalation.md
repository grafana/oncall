---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/escalation/
title: Escalation HTTP API
weight: 0
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
  manual-paging:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/manual
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/configure/integrations/references/manual
  manual-paging-team-important:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/manual#important-escalations
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/configure/integrations/references/manual#important-escalations
---

# Escalation HTTP API

**Required permission**: `grafana-oncall-app.alert-groups:direct-paging` (user authentication only)

See [Manual paging integration](ref:manual-paging) for more background on how escalating to a team or user(s) works.

## Escalate to a set of users

For more details about how to fetch a user's Grafana OnCall ID, refer to the [Users](ref:users) public API documentation.

```shell
curl "{{API_URL}}/api/v1/escalation/" \
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
  "id": "IZHCC4GTNPZ93",
  "integration_id": "CC3GZYZNIIEH5",
  "route_id": "RDN8LITALJXCJ",
  "alerts_count": 1,
  "state": "firing",
  "created_at": "2024-08-15T18:05:36.801215Z",
  "resolved_at": null,
  "resolved_by": null,
  "acknowledged_at": null,
  "acknowledged_by": null,
  "title": "We're seeing a network outage in the datacenter",
  "permalinks": {
    "slack": null,
    "slack_app": null,
    "telegram": null,
    "web": "http://<my_grafana_url>/a/grafana-oncall-app/alert-groups/I5LAZ2MXGPUAH"
  },
  "silenced_at": null
}
```

## Escalate to a team

For more details about how to fetch a team's Grafana OnCall ID, refer to the [Teams](ref:teams) public API documentation.

```shell
curl "{{API_URL}}/api/v1/escalation/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
    "title": "We are seeing a network outage in the datacenter",
    "message": "I need help investigating, can you join the investigation?",
    "source_url": "https://github.com/myorg/myrepo/issues/123",
    "team": "TI73TDU19W48J",
    "important_team_escalation": true
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "IZHCC4GTNPZ93",
  "integration_id": "CC3GZYZNIIEH5",
  "route_id": "RDN8LITALJXCJ",
  "alerts_count": 1,
  "state": "firing",
  "created_at": "2024-08-15T18:05:36.801215Z",
  "resolved_at": null,
  "resolved_by": null,
  "acknowledged_at": null,
  "acknowledged_by": null,
  "title": "We're seeing a network outage in the datacenter",
  "permalinks": {
    "slack": null,
    "slack_app": null,
    "telegram": null,
    "web": "http://<my_grafana_url>/a/grafana-oncall-app/alert-groups/I5LAZ2MXGPUAH"
  },
  "silenced_at": null
}
```

## Escalate to a set of user(s) for an existing Alert Group

The following shows how you can escalate to a set of user(s) for an existing Alert Group.

```shell
curl "{{API_URL}}/api/v1/escalation/" \
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
  "id": "IZHCC4GTNPZ93",
  "integration_id": "CC3GZYZNIIEH5",
  "route_id": "RDN8LITALJXCJ",
  "alerts_count": 1,
  "state": "firing",
  "created_at": "2024-08-15T18:05:36.801215Z",
  "resolved_at": null,
  "resolved_by": null,
  "acknowledged_at": null,
  "acknowledged_by": null,
  "title": "We're seeing a network outage in the datacenter",
  "permalinks": {
    "slack": null,
    "slack_app": null,
    "telegram": null,
    "web": "http://<my_grafana_url>/a/grafana-oncall-app/alert-groups/I5LAZ2MXGPUAH"
  },
  "silenced_at": null
}
```

| Parameter            | Unique |     Required     | Description                                                                                                                                                                                                                                         |
| -------------------- | :----: | :--------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`               |  No   |       No        | Name of the Alert Group that will be created                                                                                                                                                                                                                                      |
| `message`               |  No   |       No        | Content of the Alert Group that will be created                                                                                                                                                                                       |
| `source_url`               |  No   |       No        | Value that will be added in the Alert's payload as `oncall.permalink`. This can be useful to have the source URL/button autopopulated with a URL of interest.                        |
| `team`               |  No   |       Yes (see [Things to Note](#things-to-note))        | Grafana OnCall team ID. If specified, will use the "Direct Paging" Integration associated with this Grafana OnCall team, to create the Alert Group.                                                                                                                                                                                        |
| `users`               |  No   |       Yes (see [Things to Note](#things-to-note))        | List of user(s) to escalate to. See above request example for object schema. `id` represents the Grafana OnCall user's ID. `important` is a boolean representing whether to escalate the Alert Group using this user's default or important personal notification policy.                                                                                                                                                                                        |
| `alert_group_id`               |  No   |       No        | If specified, will escalate the specified users for this Alert Group.                                                                                                                                                                                         |
| `important_team_escalation`               |  No   |       No        | Sets the value of `payload.oncall.important` to the value specified here (default is `False`; see [Things to Note](#things-to-note) for more details). |

## Things to note

- `team` and `users` are mutually exclusive in the request payload. If you would like to escalate to a team AND user(s),
first escalate to a team, then using the Alert Group ID returned in the response payload, add the required users to the
existing Alert Group
- `alert_group_id` is mutually exclusive with `title`, `message`, and `source_url`. Practically speaking this means that
if you are trying to escalate to a set of users on an existing Alert Group, you cannot update the `title`, `message`, or
`source_url` of that Alert Group
- If escalating to a set of users for an existing Alert Group, the Alert Group cannot be in a resolved state
- Regarding `important_team_escalation`; this can be useful to send an "important" escalation to the specified team.
Teams can configure their Direct Paging Integration to route to different escalation chains based on the value of
`payload.oncall.important`. See [Manual paging integration - important escalations](ref:manual-paging-team-important)
for more details.

**HTTP request**

`POST {{API_URL}}/api/v1/escalation/`
