---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/organizations/
title: Grafana OnCall organizations HTTP API
weight: 0
refs:
  pagination:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/oncall-api-reference/#pagination
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/#pagination
---

# Grafana OnCall organizations HTTP API

## Get an organization

**Required permission**: `grafana-oncall-app.other-settings:read`

This endpoint retrieves the organization object.

```shell
curl "{{API_URL}}/api/v1/organizations/O53AAGWFBPE5W/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
````

The above command returns JSON structured in the following way:

```json
{
  "id": "O53AAGWFBPE5W"
}
```

**HTTP request**

`GET {{API_URL}}/api/v1/organizations/<ORGANIZATION_ID>/`

| Parameter  | Unique  | Description                                                        |
| ---------- | :-----: | :----------------------------------------------------------------- |
| `id`       | Yes | Organization ID                                                            |

## List Organizations

**Required permission**: `grafana-oncall-app.other-settings:read`

```shell
curl "{{API_URL}}/api/v1/organizations/" \
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
      "id": "O53AAGWFBPE5W"
    }
  ],
  "page_size": 25,
  "current_page_number": 1,
  "total_pages": 1
}
```

> **Note**: The response is [paginated](ref:pagination). You may need to make multiple requests to get all records.

**HTTP request**

`GET {{API_URL}}/api/v1/organizations/`
