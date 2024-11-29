---
title: Advanced template configuration
menuTitle: Advanced templates
description: Understand advanced configuration options for alert templates in OnCall.
weight: 400
keywords:
  - OnCall
  - Configuration
  - Webhooks
  - JSON
  - Alert payload
  - Conditions
  - Advanced templates
canonical: https://grafana.com/docs/oncall/latest/configure/jinja2-templating/advanced-templates/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating/advanced-templates/
  - ../jinja2-templating/advanced-templates/ # /docs/oncall/<ONCALL_VERSION>/jinja2-templating/advanced-templates/
refs:
  map-payloads-to-oncall-fields:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating/#map-payloads-to-oncall-fields
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating/#map-payloads-to-oncall-fields
---

# Advanced template configuration

Grafana OnCall uses the [Jinja templating language](http://jinja.pocoo.org/docs/2.10/) to
format alert groups for various platforms such as the Web, Slack, phone calls, SMS messages, and more.
This allows you to customize the presentation and content of alerts when they are triggered.

Jinja2 offers a range of functionalities, including loops, conditions, and functions, which can be used to enhance alert template customization.
Every alert from a monitoring system is received in a key/value format, which Grafana OnCall maps to specific fields, such as:
`title`, `message`, `image`, `grouping`, and `auto-resolve`.

To learn more about mapping your alert payload to Grafana OnCall fields, refer to [map payloads to  OnCall fields](ref:map-payloads-to-oncall-fields).

## Loops

Monitoring systems can send an array of values. Use Jinja to iterate and format the alert payloads. For example:

```.jinja2
*Values:*
 {% for evalMatch in payload.evalMatches -%}
 `{{ evalMatch['metric'] }}: '{{ evalMatch['value'] -}}'`{{ " " }}
 {%- endfor %}
```

## Conditions

Add conditional instructions based on specific alert rules. For instance, to provide instructions when an alert comes from a specific Grafana alert rule:

````jinja2
{% if  payload.ruleId == '1' -%}
*Alert TODOs*
1. Get access to the container
    ```
        kubectl port-forward service/example 3000:80
    ```
2. Check for the exception.
3. Open the container and reload caches.
4. Click Custom Button `Send to Jira`
{%- endif -%}
````

## Built-in Jinja functions

Jinja2 includes various built-in functions that can be used in Grafana OnCall. For example, to prettify JSON:

```.jinja2
{{ payload | tojson_pretty }}
```

Some commonly used built-in functions include:

- `abs`
- `capitalize`
- `trim`

For a full list of Jinja built-in functions, see the
[Jinja documentation on GitHub](https://github.com/pallets/jinja/blob/3915eb5c2a7e2e4d49ebdf0ecb167ea9c21c60b2/src/jinja2/filters.py#L1307)

## Functions added by Grafana OnCall

Grafana OnCall enhances Jinja with additional functions:

- `time`: Current time
- `tojson`: Dumps a structure to JSON
- `tojson_pretty`: Same as `tojson`, but prettified
- `iso8601_to_time`: Converts ISO8601 time (`2015-02-17T18:30:20.000Z`) to datetime
- `datetimeformat`: Converts datetime to string according to strftime format codes (`%H:%M / %d-%m-%Y` by default)
- `datetimeformat_as_timezone`: Converts datetime to string with timezone conversion (`UTC` by default)
  - Usage example: `{{ payload.alerts.startsAt | iso8601_to_time | datetimeformat_as_timezone('%Y-%m-%dT%H:%M:%S%z', 'America/Chicago') }}`
- `datetimeparse`: Converts string to datetime according to strftime format codes (`%H:%M / %d-%m-%Y` by default)
- `timedeltaparse`: Converts a time range (e.g., `5s`, `2m`, `6h`, `3d`) to a timedelta that can be added to or subtracted from a datetime
  - Usage example: `{% set delta = alert.window | timedeltaparse %}{{ alert.startsAt | iso8601_to_time - delta | datetimeformat }}`
- `timestamp_to_datetime`: Converts a Unix/Epoch time to a datetime object
- `regex_replace`: Performs a regex find and replace
- `regex_match`: Performs a regex match, returns `True` or `False`
  - Usage example: `{{ payload.ruleName | regex_match(".*") }}`
- `regex_search`: Performs a regex search, returns `True` or `False`
  - Usage example: `{{ payload.message | regex_search("Severity: (High|Critical)") }}`
- `b64decode`: Performs a base64 string decode
  - Usage example: `{{ payload.data | b64decode }}`
- `parse_json`:Parses a JSON string to an object
  - Usage example: `{{ (payload.data | b64decode | parse_json).name }}`
