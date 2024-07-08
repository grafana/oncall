---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/resolution_notes/
title: Resolution notes HTTP API
weight: 900
---

# Resolution notes HTTP API

## Create a resolution note

```shell
curl "{{API_URL}}/api/v1/resolution_notes/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "alert_group_id": "I68T24C13IFW1",
      "text": "Demo resolution note"
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
  "text": "Demo resolution note"
}
```

| Parameter        | Required | Description          |
| ---------------- | :------: | :------------------- | --- |
| `alert_group_id` |   Yes    | Alert group ID       |     |
| `text`           |   Yes    | Resolution note text |

**HTTP request**

`POST {{API_URL}}/api/v1/resolution_notes/`

## Get a resolution note

```shell
curl "{{API_URL}}/api/v1/resolution_notes/M4BTQUS3PRHYQ/" \
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
  "text": "Demo resolution note"
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/resolution_notes/<RESOLUTION_NOTE_ID>/`

## List resolution notes

```shell
curl "{{API_URL}}/api/v1/resolution_notes/" \
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
      "text": "Demo resolution note"
    }
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
}
```

The following available filter parameter should be provided as a `GET` argument:

- `alert_group_id`

**HTTP request**

`GET {{API_URL}}/api/v1/resolution_notes/`

## Update a resolution note

```shell
curl "{{API_URL}}/api/v1/resolution_notes/M4BTQUS3PRHYQ/" \
  --request PUT \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "text": "Demo resolution note updated"
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
  "text": "Demo resolution note updated"
}
```

**HTTP request**

`PUT {{API_URL}}/api/v1/resolution_notes/<RESOLUTION_NOTE_ID>/`

## Delete a resolution note

```shell
curl "{{API_URL}}/api/v1/resolution_notes/M4BTQUS3PRHYQ/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow"
```

**HTTP request**

`DELETE {{API_URL}}/api/v1/resolution_notes/<RESOLUTION_NOTE_ID>/`
