---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/escalation_chains/
title: Escalation chains HTTP API
weight: 200
---

# Escalation chains HTTP API

## Create an escalation chain

```shell
curl "{{API_URL}}/api/v1/escalation_chains/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "name": "example-chain"
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "FWDL7M6N6I9HE",
  "name": "example-chain",
  "team_id": null
}
```

| Parameter | Required | Description                  |
| --------- | :------: | :--------------------------- |
| name      |   yes    | Name of the escalation chain |
| team_id   |    no    | ID of the team               |

**HTTP request**

`POST {{API_URL}}/api/v1/escalation_chains/`

## Get an escalation chain

```shell
curl "{{API_URL}}/api/v1/escalation_chains/F5JU6KJET33FE/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "id": "F5JU6KJET33FE",
  "name": "default",
  "team_id": null
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/escalation_chains/<ESCALATION_CHAIN_ID>/`

## List escalation chains

```shell
curl "{{API_URL}}/api/v1/escalation_chains/" \
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
      "id": "F5JU6KJET33FE",
      "name": "default",
      "team_id": null
    }
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/escalation_chains/`

## Delete an escalation chain

```shell
curl "{{API_URL}}/api/v1/escalation_chains/F5JU6KJET33FE/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

**HTTP request**

`DELETE {{API_URL}}/api/v1/escalation_chains/<ESCALATION_CHAIN_ID>/`
