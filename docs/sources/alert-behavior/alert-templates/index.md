---
aliases:
  - ../integrations/create-custom-templates/
  - /docs/oncall/latest/alert-behavior/alert-templates/
canonical: https://grafana.com/docs/oncall/latest/alert-behavior/alert-templates/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - Jinja
title: Configure alert templates
weight: 300
---

# Configure alert templates

Grafana OnCall can integrate with any monitoring systems that can send alerts using webhooks with JSON payloads. By
default, webhooks deliver raw JSON payloads. When Grafana OnCall receives an alert and parses its payload, a default
pre configured alert template is applied to modify the alert payload to be more human readable. These alert templates
are customizable for any integration.

See Format alerts with alert templates in this document to learn more about how to customize alert templates.

## Alert Behavior

Once Grafana OnCall receives an alert, the following occurs, based on the alert content:

- Default or customized alert templates are applied to deliver the most useful alert fields with the most valuable information,
  in a readable format.
- Alerts are grouped based on your alert grouping configurations, combining similar or related alerts to reduce alert noise.
- Alerts automatically resolve if an alert from the monitoring system matches the resolve condition for that alert.

## Alert payload

Alerts received by Grafana OnCall contain metadata as keys and values in a JSON object. The following is an example of
an alert from Grafana OnCall:

```json
{
  "dashboardId": 1,
  "title": "[Alerting] Panel Title alert",
  "message": "Notification Message",
  "evalMatches": [
    {
      "value": 1,
      "metric": "Count",
      "tags": {}
    }
  ],
  "imageUrl": "https://grafana.com/static/assets/img/blog/mixed_styles.png",
  "orgId": 1,
  "panelId": 2,
  "ruleId": 1,
  "ruleName": "Panel Title alert",
  "ruleUrl": "http://localhost:3000/d/hZ7BuVbWz/test-dashboard?fullscreen\u0026edit\u0026tab=alert\u0026panelId=2\u0026orgId=1",
  "state": "alerting",
  "tags": {
    "tag name": "tag value"
  }
}
```

In Grafana OnCall every alert and alert group has the following fields:

- `Title`, `message` and `image url`
- `Grouping Id`
- `Resolve Signal`

The JSON payload is converted. For example:

- `{{ payload.title }}` -> Title
- `{{ payload.message }}` -> Message
- `{{ payload.imageUrl }}` -> Image Url

The result is that each field of the alert in OnCall is now mapped to the JSON payload keys. This also true for the
alert behavior:

- `{{ payload.ruleId }}` -> Grouping Id
- `{{ 1 if payload.state == 'OK' else 0 }}` -> Resolve Signal

Grafana OnCall provides a pre configured default Jinja template for supported integrations. If your monitoring system is
not in the Grafana OnCall integrations list, you can create a generic `webhook` integration, send an alert, and configure
your templates.

## Customize alerts with alert templates

Alert templates allow you to format any alert fields recognized by Grafana OnCall. You can customize default alert
templates for all the different ways you receive your alerts such as web, slack, SMS, and email. For more advanced
customization, use Jinja templates.

As a best practice, add _Playbooks_, _Useful links_, or _Checklists_ to the alert message.

To customize alert templates in Grafana OnCall:

1. Navigate to the **Integrations** tab, select the integration, then click **Change alert template and grouping**.

2. In Alert Templates, select a template from the **Edit template for** dropdown.

3. Edit the Appearances template as needed:

   - `Title`, `Message`, `Image url` for Web
   - `Title`, `Message`, `Image url` for Slack
   - `Title` used for SMS
   - `Title` used for Phone
   - `Title`, `Message` used for Email

4. Edit the alert behavior as needed:
   - `Grouping Id` - This output groups other alerts into a single alert group.
   - `Acknowledge Condition` - The output should be `ok`, `true`, or `1` to auto-acknowledge the alert group.
     For example, `{{ 1 if payload.state == 'OK' else 0 }}`.
   - `Resolve Condition` - The output should be `ok`, `true` or `1` to auto-resolve the alert group.
     For example, `{{ 1 if payload.state == 'OK' else 0 }}`.
   - `Source Link` - Used to customize the URL link to provide as the "source" of the alert.

## Advanced Jinja templates

Grafana OnCall uses [Jinja templating language](http://jinja.pocoo.org/docs/2.10/) to format alert groups for the Web,
Slack, phone calls, SMS messages, and more because the JSON format is not easily readable by humans. As a result, you
can decide what you want to see when an alert group is triggered as well as how it should be presented.

Jinja2 offers simple but multi-faceted functionality by using loops, conditions, functions, and more.

> **NOTE:** Every alert from a monitoring system comes in the key/value format.

Grafana OnCall has rules about which of the keys match to: `__title`, `message`, `image`, `grouping`, and `auto-resolve__`.

### Loops

Monitoring systems can send an array of values. In this example, you can use Jinja to iterate and format the alert
using a Grafana example:

```.jinja2
*Values:*
 {% for evalMatch in payload.evalMatches -%}
 `{{ evalMatch['metric'] }}: '{{ evalMatch['value'] -}}'`{{ " " }}
 {%- endfor %}
```

### Conditions

You can add instructions if an alert comes from a specified Grafana alert rule:

````jinja2
{% if  payload.ruleId == '1' -%}
*Alert TODOs*
1. Get acess to the container
    ```
        kubectl port-forward service/example 3000:80
    ```
2. Check for the exception.
3. Open the container and reload caches.
4. Click Custom Button `Send to Jira`
{%- endif -%}
````

### Built-in Jinja functions

Jinja2 includes built-in functions that can also be used in Grafana OnCall. For example:

```.jinja2
{{ payload | tojson_pretty }}
```

Built-in functions:

- `abs`
- `capitalize`
- `trim`
- You can see the full list of Jinja built-in functions on github [here](https://github.com/pallets/jinja/blob/3915eb5c2a7e2e4d49ebdf0ecb167ea9c21c60b2/src/jinja2/filters.py#L1307)

### Functions added by Grafana OnCall

- `time` - current time
- `tojson_pretty` - JSON prettified
- `iso8601_to_time` - converts time from iso8601 (`2015-02-17T18:30:20.000Z`) to datetime
- `datetimeformat` - converts time from datetime to the given format (`%H:%M / %d-%m-%Y` by default)
- `regex_replace` - performs a regex find and replace
- `regex_match` - performs a regex match, returns `True` or `False`. Usage example: `{{ payload.ruleName | regex_match(".*") }}`
