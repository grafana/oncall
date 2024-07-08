---
title: Grafana OnCall HTTP API reference
menuTitle: API reference
description: Reference material for Grafana OnCall API.
weight: 900
keywords:
  - OnCall
  - API
  - HTTP
  - API key
canonical: https://grafana.com/docs/oncall/latest/oncall-api-reference/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/
---

# HTTP API Reference

Use the following guidelines for the Grafana OnCall API.

<!--Welcome to the Grafana OnCall API reference!

| Simplified API Structure |
| ----------- |
| ![Grafana OnCall API Scheme](images/scheme.jpg) | -->

## Authentication

To authorize, use the **Authorization** header:

```shell
# With shell, you can just pass the correct header with each request
curl "api_endpoint_here" --header "Authorization: "api_key_here""
```

Grafana OnCall uses API keys to allow access to the API. You can request a new OnCall API key in OnCall -> Settings page.

An API key is specific to a user and a Grafana stack. If you want to switch to a different stack configuration,
request a different API key.

The endpoint refers to the OnCall Application endpoint and can be found on the OnCall -> Settings page as well.

## Pagination

List endpoints such as List Integrations or List Alert Groups return multiple objects.

The OnCall API returns them in pages. Note that the page size may vary.

| Parameter  |                                            Meaning                                            |
| ---------- | :-------------------------------------------------------------------------------------------: |
| `count`    |        The total number of items. It can be `0` if a request does not return any data.        |
| `next`     |     A link to the next page. It can be `null` if the next page does not contain any data.     |
| `previous` | A link to the previous page. It can be `null` if the previous page does not contain any data. |
| `results`  |               The data list. Can be `[]` if a request does not return any data.               |

## Rate Limits

Grafana OnCall provides rate limits to ensure alert group notifications will be delivered to your Slack workspace even
when some integrations produce a large number of alerts.

### Monitoring integrations Rate Limits

Rate limited response HTTP status: 429

| Scope                        | Amount | Time Frame |
| ---------------------------- | :----: | :--------: |
| Alerts from each integration |  300   | 5 minutes  |
| Alerts from the whole organization   |  500   | 5 minutes  |

## API rate limits

You can reduce or increase rate limits depending on platform status.

| Scope                    | Amount | Time Frame |
| ------------------------ | :----: | :--------: |
| API requests per API key |  300   | 5 minutes  |
