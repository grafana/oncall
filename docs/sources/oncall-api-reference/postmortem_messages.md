---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/postmortem_messages/
draft: true
title: Postmortem Messages HTTP API
weight: 900
---

# Create a postmortem message

```shell
curl "{{API_URL}}/api/v1/postmortem_messages/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "alert_group_id": "I68T24C13IFW1",
      "text": "Demo postmortem message"
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "M4BTQUS3PRHYQ",
  "alert_group_id": "I68T24C13IFW1",
  "author": "U4DNY931HHJS5",
  "source": "web",
  "created_at": "2020-06-19T12:40:01.429805Z",
  "text": "Demo postmortem message"
}
```

**HTTP request**

`POST {{API_URL}}/api/v1/postmortem_messages/`

# Get a postmortem message

```shell
curl "{{API_URL}}/api/v1/postmortem_messages/M4BTQUS3PRHYQ/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "id": "M4BTQUS3PRHYQ",
  "alert_group_id": "I68T24C13IFW1",
  "author": "U4DNY931HHJS5",
  "source": "web",
  "created_at": "2020-06-19T12:40:01.429805Z",
  "text": "Demo postmortem message"
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/postmortem_messages/<POSTMORTEM_MESSAGE_ID>/`

# List postmortem messages

```shell
curl "{{API_URL}}/api/v1/postmortem_messages/" \
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
      "id": "M4BTQUS3PRHYQ",
      "alert_group_id": "I68T24C13IFW1",
      "author": "U4DNY931HHJS5",
      "source": "web",
      "created_at": "2020-06-19T12:40:01.429805Z",
      "text": "Demo postmortem message"
    }
  ]
}
```

The following available filter parameter should be provided as a `GET` argument:

- `alert_group_id`

**HTTP request**

`GET {{API_URL}}/api/v1/postmortem_messages/`

# Update a postmortem message

```shell
curl "{{API_URL}}/api/v1/postmortem_messages/M4BTQUS3PRHYQ/" \
  --request PUT \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "text": "Demo postmortem message"
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "M4BTQUS3PRHYQ",
  "alert_group_id": "I68T24C13IFW1",
  "author": "U4DNY931HHJS5",
  "source": "web",
  "created_at": "2020-06-19T12:40:01.429805Z",
  "text": "Demo postmortem message"
}
```

**HTTP request**

`PUT {{API_URL}}/api/v1/postmortem_messages/<POSTMORTEM_MESSAGE_ID>/`

# Delete a postmortem message

```shell
curl "{{API_URL}}/api/v1/postmortem_messages/M4BTQUS3PRHYQ/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow"
```

**HTTP request**

`DELETE {{API_URL}}/api/v1/postmortem_messages/<POSTMORTEM_MESSAGE_ID>/`
