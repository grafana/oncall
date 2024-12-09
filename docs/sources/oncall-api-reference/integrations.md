---
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/integrations/
title: Integrations HTTP API
weight: 0
refs:
  alertmanager:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/alertmanager/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/alertmanager/
  pagination:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/oncall-api-reference/#pagination
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/#pagination
---

# Integrations HTTP API

{{< admonition type="note" >}}
⚠️ `msteams` templates are only available on Grafana Cloud
{{< /admonition >}}

## Create an integration

**Required permission**: `grafana-oncall-app.integrations:write`

```shell
curl "{{API_URL}}/api/v1/integrations/" \
  --request POST \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "type":"grafana"
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "CFRPV98RPR1U8",
  "name": "Grafana :blush:",
  "team_id": null,
  "link": "{{API_URL}}/integrations/v1/grafana/mReAoNwDm0eMwKo1mTeTwYo/",
  "inbound_email": null,
  "type": "grafana",
  "default_route": {
    "id": "RVBE4RKQSCGJ2",
    "escalation_chain_id": "F5JU6KJET33FE",
    "slack": {
      "channel_id": "CH23212D"
    }
  },
  "templates": {
    "grouping_key": null,
    "resolve_signal": null,
    "acknowledge_signal": null,
    "source_link": null,
    "slack": {
      "title": null,
      "message": null,
      "image_url": null
    },
    "web": {
      "title": null,
      "message": null,
      "image_url": null
    },
    "sms": {
      "title": null
    },
    "phone_call": {
      "title": null
    },
    "telegram": {
      "title": null,
      "message": null,
      "image_url": null
    },
    "mobile_app": {
      "title": null,
      "message": null
    },
    "email": {
      "title": null,
      "message": null
    },
    "msteams": {
      "title": null,
      "message": null,
      "image_url": null
    }
  }
}
```

Integrations are sources of alerts and alert groups for Grafana OnCall.
For example, to learn how to integrate Grafana OnCall with Alertmanager refer to [Alertmanager](ref:alertmanager).

**HTTP request**

`POST {{API_URL}}/api/v1/integrations/`

## Get integration

**Required permission**: `grafana-oncall-app.integrations:read`

```shell
curl "{{API_URL}}/api/v1/integrations/CFRPV98RPR1U8/" \
  --request GET \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json"
```

The above command returns JSON structured in the following way:

```json
{
  "id": "CFRPV98RPR1U8",
  "name": "Grafana :blush:",
  "team_id": null,
  "link": "{{API_URL}}/integrations/v1/grafana/mReAoNwDm0eMwKo1mTeTwYo/",
  "inbound_email": null,
  "type": "grafana",
  "default_route": {
    "id": "RVBE4RKQSCGJ2",
    "escalation_chain_id": "F5JU6KJET33FE",
    "slack": {
      "channel_id": "CH23212D"
    }
  },
  "templates": {
    "grouping_key": null,
    "resolve_signal": null,
    "acknowledge_signal": null,
    "source_link": null,
    "slack": {
      "title": null,
      "message": null,
      "image_url": null
    },
    "web": {
      "title": null,
      "message": null,
      "image_url": null
    },
    "sms": {
      "title": null
    },
    "phone_call": {
      "title": null
    },
    "telegram": {
      "title": null,
      "message": null,
      "image_url": null
    },
    "mobile_app": {
      "title": null,
      "message": null
    },
    "email": {
      "title": null,
      "message": null
    },
    "msteams": {
      "title": null,
      "message": null,
      "image_url": null
    }
  }
}
```

This endpoint retrieves an integration. Integrations are sources of alerts and alert groups for Grafana OnCall.

**HTTP request**

`GET {{API_URL}}/api/v1/integrations/<INTEGRATION_ID>/`

## List integrations

**Required permission**: `grafana-oncall-app.integrations:read`

```shell
curl "{{API_URL}}/api/v1/integrations/" \
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
      "id": "CFRPV98RPR1U8",
      "name": "Grafana :blush:",
      "team_id": null,
      "link": "{{API_URL}}/integrations/v1/grafana/mReAoNwDm0eMwKo1mTeTwYo/",
      "inbound_email": null,
      "type": "grafana",
      "default_route": {
        "id": "RVBE4RKQSCGJ2",
        "escalation_chain_id": "F5JU6KJET33FE",
        "slack": {
          "channel_id": "CH23212D"
        }
      },
      "templates": {
        "grouping_key": null,
        "resolve_signal": null,
        "acknowledge_signal": null,
        "source_link": null,
        "slack": {
          "title": null,
          "message": null,
          "image_url": null
        },
        "web": {
          "title": null,
          "message": null,
          "image_url": null
        },
        "sms": {
          "title": null
        },
        "phone_call": {
          "title": null
        },
        "telegram": {
          "title": null,
          "message": null,
          "image_url": null
        },
        "mobile_app": {
          "title": null,
          "message": null
        },
        "email": {
          "title": null,
          "message": null
        },
        "msteams": {
          "title": null,
          "message": null,
          "image_url": null
        }
      }
    }
  ],
  "current_page_number": 1,
  "page_size": 50,
  "total_pages": 1
}
```

> **Note**: The response is [paginated](ref:pagination). You may need to make multiple requests to get all records.

**HTTP request**

`GET {{API_URL}}/api/v1/integrations/`

## Update integration

**Required permission**: `grafana-oncall-app.integrations:write`

```shell
curl "{{API_URL}}/api/v1/integrations/CFRPV98RPR1U8/" \
  --request PUT \
  --header "Authorization: meowmeowmeow" \
  --header "Content-Type: application/json" \
  --data '{
      "templates": {
          "grouping_key": null,
          "resolve_signal": null,
          "slack": {
             "title": null,
             "message": null,
             "image_url": null
          }
      }
  }'
```

The above command returns JSON structured in the following way:

```json
{
  "id": "CFRPV98RPR1U8",
  "name": "Grafana :blush:",
  "team_id": null,
  "link": "{{API_URL}}/integrations/v1/grafana/mReAoNwDm0eMwKo1mTeTwYo/",
  "inbound_email": null,
  "type": "grafana",
  "default_route": {
    "id": "RVBE4RKQSCGJ2",
    "escalation_chain_id": "F5JU6KJET33FE",
    "slack": {
      "channel_id": "CH23212D"
    }
  },
  "templates": {
    "grouping_key": null,
    "resolve_signal": null,
    "slack": {
      "title": null,
      "message": null,
      "image_url": null
    },
    "web": {
      "title": null,
      "message": null,
      "image_url": null
    },
    "email": {
      "title": null,
      "message": null
    },
    "sms": {
      "title": null
    },
    "phone_call": {
      "title": null
    },
    "telegram": {
      "title": null,
      "message": null,
      "image_url": null
    },
    "mobile_app": {
      "title": null,
      "message": null
    }
  }
}
```

**HTTP request**

`PUT {{API_URL}}/api/v1/integrations/<INTEGRATION_ID>/`

## Delete integration

**Required permission**: `grafana-oncall-app.integrations:write`

Deleted integrations will stop recording new alerts from monitoring. Integration removal won't trigger removal of
related alert groups or alerts.

```shell
curl "{{API_URL}}/api/v1/integrations/CFRPV98RPR1U8/" \
  --request DELETE \
  --header "Authorization: meowmeowmeow"
```

**HTTP request**

`DELETE {{API_URL}}/api/v1/integrations/<INTEGRATION_ID>/`
