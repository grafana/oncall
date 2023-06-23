---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/postmortems/
draft: true
title: Postmortem HTTP API
weight: 1000
---

# Create a postmortem

```shell
curl "{{API_URL}}/api/v1/postmortems/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "alert_group_id": "I68T24C13IFW1",
      "text": "Demo postmortem text"
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "P658FE5K87EWZ",
  "alert_group_id": "I68T24C13IFW1",
  "created_at": "2020-06-19T12:37:01.430444Z",
  "text": "Demo postmortem text"
}
```

**HTTP request**

`POST {{API_URL}}/api/v1/postmortems/`

# Get a postmortem

```shell
curl "{{API_URL}}/api/v1/postmortems/P658FE5K87EWZ/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "id": "P658FE5K87EWZ",
  "alert_group_id": "I68T24C13IFW1",
  "created_at": "2020-06-19T12:37:01.430444Z",
  "text": "Demo postmortem text",
  "postmortem_messages": [
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

**HTTP request**

`GET {{API_URL}}/api/v1/postmortems/<POSTMORTEM_ID>/`

# List postmortems

```shell
curl "{{API_URL}}/api/v1/postmortems/" \
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
      "id": "P658FE5K87EWZ",
      "alert_group_id": "I68T24C13IFW1",
      "created_at": "2020-06-19T12:37:01.430444Z",
      "text": "Demo postmortem text",
      "postmortem_messages": [
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
  ]
}
```

The following available filter parameter should be provided with a `GET` argument:

- `alert_group_id`

**HTTP request**

`GET {{API_URL}}/api/v1/postmortems/`

# Update a postmortem

```shell
curl "{{API_URL}}/api/v1/postmortems/P658FE5K87EWZ/" \
  --request PUT \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "text": "Demo postmortem text"
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "P658FE5K87EWZ",
  "alert_group_id": "I68T24C13IFW1",
  "created_at": "2020-06-19T12:37:01.430444Z",
  "text": "Demo postmortem text"
}
```

**HTTP request**

`PUT {{API_URL}}/api/v1/postmortems/<POSTMORTEM_ID>/`

# Delete a postmortem

```shell
curl "{{API_URL}}/api/v1/postmortems/P658FE5K87EWZ/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow"
```

**HTTP request**

`DELETE {{API_URL}}/api/v1/postmortems/<POSTMORTEM_ID>/`
