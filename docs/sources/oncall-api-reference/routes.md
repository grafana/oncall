---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/routes/
title: Routes HTTP API
weight: 1100
---

# Routes HTTP API

## Create a route

```shell
curl "{{API_URL}}/api/v1/routes/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "integration_id": "CFRPV98RPR1U8",
      "escalation_chain_id": "F5JU6KJET33FE",
      "routing_regex": "us-(east|west)",
      "position": 0,
      "slack": {
        "channel_id": "CH23212D"
      }
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "RIYGUJXCPFHXY",
  "integration_id": "CFRPV98RPR1U8",
  "escalation_chain_id": "F5JU6KJET33FE",
  "routing_regex": "us-(east|west)",
  "position": 0,
  "is_the_last_route": false,
  "slack": {
    "channel_id": "CH23212D"
  }
}
```

Routes allow you to direct different alerts to different messenger channels and escalation chains. Useful for:

- Important/non-important alerts
- Alerts for different engineering groups
- Snoozing spam & debugging alerts

| Parameter             | Unique | Required | Description                                                                                                                                                                                                                                                                                 |
| --------------------- | :----: | :------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `integration_id`      |   No   |   Yes    | Each route is assigned to a specific integration.                                                                                                                                                                                                                                           |
| `escalation_chain_id` |   No   |   Yes    | Each route is assigned a specific escalation chain. Explicitly pass `null` to create a route without an escalation chain assigned.                                                                                                                                                          |
| `routing_type`        |  Yes   |    No    | Routing type that can be either `jinja2` or `regex`(default value)                                                                                                                                                                                                                          |
| `routing_regex`       |  Yes   |   Yes    | Jinja2 template or Python Regex query (use <https://regex101.com/> for debugging). OnCall chooses the route for an alert in case there is a match inside the whole alert payload.                                                                                                           |
| `position`            |  Yes   | Optional | Route matching is performed one after another starting from position=`0`. Position=`-1` will put the route to the end of the list before `is_the_last_route`. A new route created with a position of an existing route will move the old route (and all following routes) down in the list. |
| `slack`               |  Yes   | Optional | Dictionary with Slack-specific settings for a route.                                                                                                                                                                                                                                        |

**HTTP request**

`POST {{API_URL}}/api/v1/routes/`

## Get a route

```shell
curl "{{API_URL}}/api/v1/routes/RIYGUJXCPFHXY/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
```

The above command returns JSON structured in the following way:

```json
{
  "id": "RIYGUJXCPFHXY",
  "integration_id": "CFRPV98RPR1U8",
  "escalation_chain_id": "F5JU6KJET33FE",
  "routing_regex": "us-(east|west)",
  "position": 0,
  "is_the_last_route": false,
  "slack": {
    "channel_id": "CH23212D"
  }
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/routes/<ROUTE_ID>/`

## List routes

```shell
curl "{{API_URL}}/api/v1/routes/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "RIYGUJXCPFHXY",
      "integration_id": "CFRPV98RPR1U8",
      "escalation_chain_id": "F5JU6KJET33FE",
      "routing_regex": "us-(east|west)",
      "position": 0,
      "is_the_last_route": false,
      "slack": {
        "channel_id": "CH23212D"
      }
    },
    {
      "id": "RVBE4RKQSCGJ2",
      "integration_id": "CFRPV98RPR1U8",
      "escalation_chain_id": "F5JU6KJET33FE",
      "routing_regex": ".*",
      "position": 1,
      "is_the_last_route": true,
      "slack": {
        "channel_id": "CH23212D"
      }
    }
  ],
  "current_page_number": 1,
  "page_size": 25,
  "total_pages": 1
}
```

The following available filter parameters should be provided as `GET` arguments:

- `integration_id`
- `routing_regex` (Exact match)

**HTTP request**

`GET {{API_URL}}/api/v1/routes/`

## Update route

```shell
curl "{{API_URL}}/api/v1/routes/RIYGUJXCPFHXY/" \
  --request PUT \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "routing_regex": "us-(east|west)",
      "position": 0,
      "slack": {
        "channel_id": "CH23212D"
      }
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "RIYGUJXCPFHXY",
  "integration_id": "CFRPV98RPR1U8",
  "escalation_chain_id": "F5JU6KJET33FE",
  "routing_regex": "us-(east|west)",
  "position": 0,
  "is_the_last_route": false,
  "slack": {
    "channel_id": "CH23212D"
  }
}
```

**HTTP request**

`PUT {{API_URL}}/api/v1/routes/<ROUTE_ID>/`

## Delete a route

```shell
curl "{{API_URL}}/api/v1/routes/RIYGUJXCPFHXY/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

**HTTP request**

`DELETE {{API_URL}}/api/v1/routes/<ROUTE_ID>/`
