---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/outgoing_webhooks/
title: Outgoing webhooks HTTP API
weight: 700
refs:
  outgoing-webhooks:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/outgoing-webhooks/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/outgoing-webhooks/
  event-types:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/outgoing-webhooks/#event-types
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/outgoing-webhooks/#event-types
---

# Outgoing webhooks

> ⚠️ A note about actions: Before version **v1.3.11** webhooks existed as actions within the API, the /actions
> endpoint remains available and is compatible with previous callers but under the hood it will interact with the
> new webhooks objects.  It is recommended to use the /webhooks endpoint going forward which has more features.

For more details about specific fields of a webhook, refer to [Outgoing webhooks](ref:outgoing-webhooks).

## List webhooks

```shell
curl "{{API_URL}}/api/v1/webhooks/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "{{WEBHOOK_UID}}",
      "name": "Demo Webhook",
      "is_webhook_enabled": true,
      "team": null,
      "data": "{\"labels\" : {{ alert_payload.commonLabels | tojson()}}}",
      "username": null,
      "password": null,
      "authorization_header": "****************",
      "trigger_template": null,
      "headers": null,
      "url": "https://example.com",
      "forward_all": false,
      "http_method": "POST",
      "trigger_type": "acknowledge",
      "integration_filter": [
        "CRV8A5MXC751A"
      ]
    }
  ],
  "page_size": 50,
  "count": 1,
  "current_page_number": 1,
  "total_pages": 1
}
```

## Get webhook

```shell
curl "{{API_URL}}/api/v1/webhooks/{{WEBHOOK_UID}}/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "id": "{{WEBHOOK_UID}}",
  "name": "Demo Webhook",
  "is_webhook_enabled": true,
  "team": null,
  "data": "{\"labels\" : {{ alert_payload.commonLabels | tojson()}}}",
  "username": null,
  "password": null,
  "authorization_header": "****************",
  "trigger_template": null,
  "headers": null,
  "url": "https://example.com",
  "forward_all": false,
  "http_method": "POST",
  "trigger_type": "acknowledge",
  "integration_filter": [
    "CRV8A5MXC751A"
  ]
}
```

## Create webhook

```shell
curl "{{API_URL}}/api/v1/webhooks/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
    "name": "New Webhook",
    "url": "https://example.com",
    "http_method": "POST",
    "trigger_type" : "resolve"
  }'
```

### Trigger Types

For more detail, refer to [Event types](ref:event-types).

- `escalation`
- `alert group created`
- `acknowledge`
- `resolve`
- `silence`
- `unsilence`
- `unresolve`
- `unacknowledge`
- `status change`

### HTTP Methods

- `POST`
- `GET`
- `PUT`
- `DELETE`
- `OPTIONS`

The above command returns JSON structured in the following way:

```json
{
  "id": "{{WEBHOOK_UID}}",
  "name": "New Webhook",
  "is_webhook_enabled": true,
  "team": null,
  "data": null,
  "username": null,
  "password": null,
  "authorization_header": null,
  "trigger_template": null,
  "headers": null,
  "url": "https://example.com",
  "forward_all": true,
  "http_method": "POST",
  "trigger_type": "resolve",
  "integration_filter": null
}
```

## Update webhook

```shell
curl "{{API_URL}}/api/v1/webhooks/{{WEBHOOK_UID}}/" \
  --request PUT \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
    "is_webhook_enabled": false
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "{{WEBHOOK_UID}}",
  "name": "New Webhook",
  "is_webhook_enabled": false,
  "team": null,
  "data": null,
  "username": null,
  "password": null,
  "authorization_header": null,
  "trigger_template": null,
  "headers": null,
  "url": "https://example.com",
  "forward_all": true,
  "http_method": "POST",
  "trigger_type": "resolve",
  "integration_filter": null
}
```

## Delete webhook

```shell
curl "{{API_URL}}/api/v1/webhooks/{{WEBHOOK_UID}}/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

## Get webhook responses

```shell
curl "{{API_URL}}/api/v1/webhooks/{{WEBHOOK_UID}}/responses" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "next": null,
  "previous": null,
  "results": [
    {
      "timestamp": "2023-08-18T16:38:23.106015Z",
      "url": "https://example.com",
      "request_trigger": "",
      "request_headers": "{\"Authorization\": \"****************\"}",
      "request_data": "{\"labels\": {\"alertname\": \"InstanceDown\", \"job\": \"node\", \"severity\": \"critical\"}}",
      "status_code": 200,
      "content": "",
      "event_data": "{\"event\": {\"type\": \"acknowledge\", \"time\": \"2023-08-18T16:38:21.442981+00:00\"}, \"user\": {\"id\": \"UK49JJNPZMFLJ\", \"username\": \"oncall\", \"email\": \"admin@localhost\"}, \"alert_group\": {\"id\": \"IZQERPWKWCGH1\", \"integration_id\": \"CRV8A5MXC751A\", \"route_id\": \"RWNCT6C77M3WM\", \"alerts_count\": 1, \"state\": \"acknowledged\", \"created_at\": \"2023-08-18T16:34:27.678406Z\", \"resolved_at\": null, \"acknowledged_at\": \"2023-08-18T16:38:21.442981Z\", \"title\": \"[firing:2] InstanceDown \", \"permalinks\": {\"slack\": null, \"telegram\": null, \"web\": \"http://localhost:3000/a/grafana-oncall-app/alert-groups/IZQERPWKWCGH1\"}}, \"alert_group_id\": \"IZQERPWKWCGH1\", \"alert_payload\": {\"alerts\": [{\"endsAt\": \"0001-01-01T00:00:00Z\", \"labels\": {\"job\": \"node\", \"group\": \"production\", \"instance\": \"localhost:8081\", \"severity\": \"critical\", \"alertname\": \"InstanceDown\"}, \"status\": \"firing\", \"startsAt\": \"2023-06-12T08:24:38.326Z\", \"annotations\": {\"title\": \"Instance localhost:8081 down\", \"description\": \"localhost:8081 of job node has been down for more than 1 minute.\"}, \"fingerprint\": \"f404ecabc8dd5cd7\", \"generatorURL\": \"\"}, {\"endsAt\": \"0001-01-01T00:00:00Z\", \"labels\": {\"job\": \"node\", \"group\": \"canary\", \"instance\": \"localhost:8082\", \"severity\": \"critical\", \"alertname\": \"InstanceDown\"}, \"status\": \"firing\", \"startsAt\": \"2023-06-12T08:24:38.326Z\", \"annotations\": {\"title\": \"Instance localhost:8082 down\", \"description\": \"localhost:8082 of job node has been down for more than 1 minute.\"}, \"fingerprint\": \"f8f08d4e32c61a9d\", \"generatorURL\": \"\"}], \"status\": \"firing\", \"version\": \"4\", \"groupKey\": \"{}:{alertname=\\\"InstanceDown\\\"}\", \"receiver\": \"combo\", \"numFiring\": 2, \"externalURL\": \"\", \"groupLabels\": {\"alertname\": \"InstanceDown\"}, \"numResolved\": 0, \"commonLabels\": {\"job\": \"node\", \"severity\": \"critical\", \"alertname\": \"InstanceDown\"}, \"truncatedAlerts\": 0, \"commonAnnotations\": {}}, \"integration\": {\"id\": \"CRV8A5MXC751A\", \"type\": \"alertmanager\", \"name\": \"One - Alertmanager\", \"team\": null}, \"notified_users\": [], \"users_to_be_notified\": []}"
    },
    {
      "timestamp": "2023-08-18T16:34:38.580574Z",
      "url": "https://example.com",
      "request_trigger": "",
      "request_headers": null,
      "request_data": "Data - Template Warning: Object of type Undefined is not JSON serializable",
      "status_code": null,
      "content": null,
      "event_data": "{\"event\": {\"type\": \"acknowledge\", \"time\": \"2023-08-18T16:34:37.940655+00:00\"}, \"user\": {\"id\": \"UK49JJNPZMFLJ\", \"username\": \"oncall\", \"email\": \"admin@localhost\"}, \"alert_group\": {\"id\": \"IZQERPWKWCGH1\", \"integration_id\": \"CRV8A5MXC751A\", \"route_id\": \"RWNCT6C77M3WM\", \"alerts_count\": 1, \"state\": \"acknowledged\", \"created_at\": \"2023-08-18T16:34:27.678406Z\", \"resolved_at\": null, \"acknowledged_at\": \"2023-08-18T16:34:37.940655Z\", \"title\": \"[firing:2] InstanceDown \", \"permalinks\": {\"slack\": null, \"telegram\": null, \"web\": \"http://localhost:3000/a/grafana-oncall-app/alert-groups/IZQERPWKWCGH1\"}}, \"alert_group_id\": \"IZQERPWKWCGH1\", \"alert_payload\": {\"alerts\": [{\"endsAt\": \"0001-01-01T00:00:00Z\", \"labels\": {\"job\": \"node\", \"group\": \"production\", \"instance\": \"localhost:8081\", \"severity\": \"critical\", \"alertname\": \"InstanceDown\"}, \"status\": \"firing\", \"startsAt\": \"2023-06-12T08:24:38.326Z\", \"annotations\": {\"title\": \"Instance localhost:8081 down\", \"description\": \"localhost:8081 of job node has been down for more than 1 minute.\"}, \"fingerprint\": \"f404ecabc8dd5cd7\", \"generatorURL\": \"\"}, {\"endsAt\": \"0001-01-01T00:00:00Z\", \"labels\": {\"job\": \"node\", \"group\": \"canary\", \"instance\": \"localhost:8082\", \"severity\": \"critical\", \"alertname\": \"InstanceDown\"}, \"status\": \"firing\", \"startsAt\": \"2023-06-12T08:24:38.326Z\", \"annotations\": {\"title\": \"Instance localhost:8082 down\", \"description\": \"localhost:8082 of job node has been down for more than 1 minute.\"}, \"fingerprint\": \"f8f08d4e32c61a9d\", \"generatorURL\": \"\"}], \"status\": \"firing\", \"version\": \"4\", \"groupKey\": \"{}:{alertname=\\\"InstanceDown\\\"}\", \"receiver\": \"combo\", \"numFiring\": 2, \"externalURL\": \"\", \"groupLabels\": {\"alertname\": \"InstanceDown\"}, \"numResolved\": 0, \"commonLabels\": {\"job\": \"node\", \"severity\": \"critical\", \"alertname\": \"InstanceDown\"}, \"truncatedAlerts\": 0, \"commonAnnotations\": {}}, \"integration\": {\"id\": \"CRV8A5MXC751A\", \"type\": \"alertmanager\", \"name\": \"One - Alertmanager\", \"team\": null}, \"notified_users\": [], \"users_to_be_notified\": []}"
    }
  ],
  "page_size": 50,
  "count": 2,
  "current_page_number": 1,
  "total_pages": 1
}
```
